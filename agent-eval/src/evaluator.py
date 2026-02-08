"""
Main evaluation engine for running agent benchmarks.
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .clients import ModelClient, GenerationConfig
from .rules import (
    check_persona_introduction,
    check_blunt_disclaimer,
    check_filler_phrases,
    check_table_overuse,
    check_repetitive_openings,
    RuleViolation,
)
from .scoring import (
    HeuristicScorer,
    LLMJudgeScorer,
    EvaluationResult,
    DimensionScore,
    ScoreDimension,
)
from .utils import load_json, load_yaml, save_json, timestamp, get_reports_dir


@dataclass
class TestScenario:
    """A single test scenario/prompt."""
    id: str
    category: str
    prompt: str
    expects_table: bool = False
    has_data_gap: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Response from an agent for a test scenario."""
    scenario_id: str
    agent_name: str
    response: str
    latency_ms: float
    token_estimate: int
    timestamp: str


@dataclass
class TestResult:
    """Complete result for a single test."""
    scenario: TestScenario
    response: AgentResponse
    rule_violations: list[RuleViolation]
    scores: dict[str, DimensionScore]
    passed: bool
    failure_reasons: list[str]


@dataclass
class EvaluationRun:
    """Complete evaluation run results."""
    run_id: str
    agent_name: str
    timestamp: str
    config: dict
    results: list[TestResult]
    aggregate_scores: dict[str, float]
    pass_rate: float
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int


class Evaluator:
    """
    Main evaluation engine that orchestrates test execution,
    rule checking, and scoring.
    """

    def __init__(
        self,
        client: ModelClient,
        agent_name: str = "custom_agent",
        config_path: str | Path | None = None,
        scenarios_path: str | Path | None = None,
        use_llm_judge: bool = False,
        judge_client: ModelClient | None = None,
    ):
        self.client = client
        self.agent_name = agent_name
        self.use_llm_judge = use_llm_judge
        self.judge_client = judge_client

        # Load config
        if config_path:
            self.config = load_yaml(config_path)
        else:
            self.config = self._default_config()

        # Load scenarios
        if scenarios_path:
            self.scenarios = self._load_scenarios(scenarios_path)
        else:
            self.scenarios = []

        # Initialize scorers
        self.heuristic_scorer = HeuristicScorer()
        self.llm_scorer = LLMJudgeScorer(judge_client) if use_llm_judge and judge_client else None

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "generation": {
                "max_tokens": 500,
                "temperature": 0.7,
            },
            "scoring": {
                "pass_threshold": 3.5,
                "weights": {
                    "naturalness": 1.0,
                    "depth_per_token": 1.0,
                    "table_judgement": 1.0,
                    "variability": 1.0,
                    "scenario_handling": 1.0,
                }
            },
            "rules": {
                "table_overuse_threshold": 0.4,
                "repetitive_opening_threshold": 0.2,
            },
            "execution": {
                "parallel": False,
                "max_workers": 4,
                "retry_on_error": True,
                "max_retries": 2,
            }
        }

    def _load_scenarios(self, path: str | Path) -> list[TestScenario]:
        """Load test scenarios from JSON file."""
        data = load_json(path)
        scenarios = []

        for item in data.get("scenarios", data if isinstance(data, list) else []):
            scenario = TestScenario(
                id=item["id"],
                category=item.get("category", "general"),
                prompt=item["prompt"],
                expects_table=item.get("expects_table", False),
                has_data_gap=item.get("has_data_gap", False),
                metadata=item.get("metadata", {}),
            )
            scenarios.append(scenario)

        return scenarios

    def add_scenario(self, scenario: TestScenario) -> None:
        """Add a single test scenario."""
        self.scenarios.append(scenario)

    def add_scenarios_from_dict(self, scenarios: list[dict]) -> None:
        """Add multiple scenarios from dict format."""
        for item in scenarios:
            self.add_scenario(TestScenario(
                id=item["id"],
                category=item.get("category", "general"),
                prompt=item["prompt"],
                expects_table=item.get("expects_table", False),
                has_data_gap=item.get("has_data_gap", False),
                metadata=item.get("metadata", {}),
            ))

    def run_single_test(
        self,
        scenario: TestScenario,
        system_prompt: str | None = None,
    ) -> TestResult:
        """Run a single test scenario."""
        gen_config = GenerationConfig(
            max_tokens=self.config["generation"]["max_tokens"],
            temperature=self.config["generation"]["temperature"],
        )

        # Generate response
        start_time = time.time()
        response_text = self.client.generate(
            prompt=scenario.prompt,
            system=system_prompt,
            config=gen_config,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Create response object
        response = AgentResponse(
            scenario_id=scenario.id,
            agent_name=self.agent_name,
            response=response_text,
            latency_ms=latency_ms,
            token_estimate=len(response_text) // 4,
            timestamp=timestamp(),
        )

        # Check rules
        violations = self._check_rules(response_text)

        # Score response
        scores = self._score_response(response_text, scenario)

        # Determine pass/fail
        passed, failure_reasons = self._evaluate_pass_fail(violations, scores)

        return TestResult(
            scenario=scenario,
            response=response,
            rule_violations=violations,
            scores=scores,
            passed=passed,
            failure_reasons=failure_reasons,
        )

    def _check_rules(self, response: str) -> list[RuleViolation]:
        """Run all rule checks on a response."""
        violations = []
        violations.extend(check_persona_introduction(response))
        violations.extend(check_blunt_disclaimer(response))
        violations.extend(check_filler_phrases(response))
        return violations

    def _score_response(
        self,
        response: str,
        scenario: TestScenario,
    ) -> dict[str, DimensionScore]:
        """Score a response across all dimensions."""
        scores = {}

        # Use heuristic scorer
        rule_result = {
            "violations": self._check_rules(response),
            "passed": True,
        }

        scores["naturalness"] = self.heuristic_scorer.score_naturalness(
            response, rule_result
        )
        scores["depth_per_token"] = self.heuristic_scorer.score_depth(
            response, scenario.prompt
        )
        scores["table_judgement"] = self.heuristic_scorer.score_table_judgement(
            response, scenario.prompt, scenario.expects_table
        )
        scores["scenario_handling"] = self.heuristic_scorer.score_scenario_handling(
            response, scenario.prompt, scenario.has_data_gap
        )

        # LLM judge scoring (if enabled)
        if self.llm_scorer:
            llm_result = self.llm_scorer.score(response, scenario.prompt)
            # Merge LLM scores (they override heuristic scores)
            for dim, score in llm_result.dimension_scores.items():
                scores[dim.value] = score

        return scores

    def _evaluate_pass_fail(
        self,
        violations: list[RuleViolation],
        scores: dict[str, DimensionScore],
    ) -> tuple[bool, list[str]]:
        """Determine if a test passed based on violations and scores."""
        failure_reasons = []
        threshold = self.config["scoring"]["pass_threshold"]

        # Check for rule violations (auto-fail)
        for violation in violations:
            if violation.severity == "error":
                failure_reasons.append(f"Rule violation: {violation.rule_name}")

        # Check score thresholds
        for dim_name, score in scores.items():
            if score.score < threshold:
                failure_reasons.append(
                    f"Low score on {dim_name}: {score.score:.2f} < {threshold}"
                )

        passed = len(failure_reasons) == 0
        return passed, failure_reasons

    def run_evaluation(
        self,
        system_prompt: str | None = None,
        scenarios: list[TestScenario] | None = None,
    ) -> EvaluationRun:
        """Run full evaluation across all scenarios."""
        test_scenarios = scenarios or self.scenarios

        if not test_scenarios:
            raise ValueError("No test scenarios provided")

        results = []

        if self.config["execution"]["parallel"]:
            results = self._run_parallel(test_scenarios, system_prompt)
        else:
            results = self._run_sequential(test_scenarios, system_prompt)

        # Check cross-response rules
        all_responses = [r.response.response for r in results]

        # Table overuse check
        table_violations = check_table_overuse(
            all_responses,
            self.config["rules"]["table_overuse_threshold"]
        )

        # Repetitive openings check
        opening_violations = check_repetitive_openings(
            all_responses,
            self.config["rules"]["repetitive_opening_threshold"]
        )

        # Add cross-response violations to all results
        for result in results:
            result.rule_violations.extend(table_violations)
            result.rule_violations.extend(opening_violations)

            # Re-evaluate pass/fail with new violations
            passed, reasons = self._evaluate_pass_fail(
                result.rule_violations, result.scores
            )
            result.passed = passed
            result.failure_reasons = reasons

        # Calculate variability score
        variability_score = self._calculate_variability(all_responses)
        for result in results:
            result.scores["variability"] = variability_score

        # Calculate aggregates
        aggregate_scores = self._calculate_aggregates(results)
        passed_count = sum(1 for r in results if r.passed)

        run_id = f"{self.agent_name}_{timestamp()}"

        return EvaluationRun(
            run_id=run_id,
            agent_name=self.agent_name,
            timestamp=timestamp(),
            config=self.config,
            results=results,
            aggregate_scores=aggregate_scores,
            pass_rate=passed_count / len(results) if results else 0,
            total_scenarios=len(results),
            passed_scenarios=passed_count,
            failed_scenarios=len(results) - passed_count,
        )

    def _run_sequential(
        self,
        scenarios: list[TestScenario],
        system_prompt: str | None,
    ) -> list[TestResult]:
        """Run tests sequentially."""
        results = []
        for scenario in scenarios:
            try:
                result = self.run_single_test(scenario, system_prompt)
                results.append(result)
            except Exception as e:
                # Create failed result on error
                results.append(self._create_error_result(scenario, str(e)))
        return results

    def _run_parallel(
        self,
        scenarios: list[TestScenario],
        system_prompt: str | None,
    ) -> list[TestResult]:
        """Run tests in parallel."""
        results = []
        max_workers = self.config["execution"]["max_workers"]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_scenario = {
                executor.submit(self.run_single_test, s, system_prompt): s
                for s in scenarios
            }

            for future in as_completed(future_to_scenario):
                scenario = future_to_scenario[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(self._create_error_result(scenario, str(e)))

        # Sort by scenario ID to maintain order
        results.sort(key=lambda r: r.scenario.id)
        return results

    def _create_error_result(
        self,
        scenario: TestScenario,
        error_msg: str,
    ) -> TestResult:
        """Create a failed result for error cases."""
        return TestResult(
            scenario=scenario,
            response=AgentResponse(
                scenario_id=scenario.id,
                agent_name=self.agent_name,
                response=f"ERROR: {error_msg}",
                latency_ms=0,
                token_estimate=0,
                timestamp=timestamp(),
            ),
            rule_violations=[],
            scores={
                "naturalness": DimensionScore(ScoreDimension.NATURALNESS, 0, "Error"),
                "depth_per_token": DimensionScore(ScoreDimension.DEPTH_PER_TOKEN, 0, "Error"),
                "table_judgement": DimensionScore(ScoreDimension.TABLE_JUDGEMENT, 0, "Error"),
                "variability": DimensionScore(ScoreDimension.VARIABILITY, 0, "Error"),
                "scenario_handling": DimensionScore(ScoreDimension.SCENARIO_HANDLING, 0, "Error"),
            },
            passed=False,
            failure_reasons=[f"Execution error: {error_msg}"],
        )

    def _calculate_variability(self, responses: list[str]) -> DimensionScore:
        """Calculate variability score across all responses."""
        if len(responses) < 2:
            return DimensionScore(
                ScoreDimension.VARIABILITY, 5.0,
                "Not enough responses to measure variability"
            )

        # Check opening diversity
        openings = []
        for resp in responses:
            first_sentence = resp.split('.')[0] if resp else ""
            # Normalize: lowercase, strip, first 50 chars
            normalized = first_sentence.lower().strip()[:50]
            openings.append(normalized)

        unique_openings = len(set(openings))
        opening_diversity = unique_openings / len(openings)

        # Check structural diversity (has table, has bullets, has numbered list)
        structures = []
        for resp in responses:
            struct = (
                '|' in resp,  # has table
                any(resp.strip().startswith(c) for c in ['-', '*', '•']),  # has bullets
                any(f"{i}." in resp[:100] for i in range(1, 10)),  # has numbered list
            )
            structures.append(struct)

        unique_structures = len(set(structures))
        structure_diversity = unique_structures / max(len(structures), 1)

        # Combined score
        combined = (opening_diversity * 0.6 + structure_diversity * 0.4)
        score = min(5.0, combined * 5)

        reasoning = (
            f"Opening diversity: {opening_diversity:.2%}, "
            f"Structure diversity: {structure_diversity:.2%}"
        )

        return DimensionScore(ScoreDimension.VARIABILITY, score, reasoning)

    def _calculate_aggregates(
        self,
        results: list[TestResult],
    ) -> dict[str, float]:
        """Calculate aggregate scores across all results."""
        if not results:
            return {}

        dimensions = ["naturalness", "depth_per_token", "table_judgement",
                     "variability", "scenario_handling"]

        aggregates = {}
        weights = self.config["scoring"]["weights"]

        for dim in dimensions:
            scores = [
                r.scores[dim].score
                for r in results
                if dim in r.scores
            ]
            if scores:
                aggregates[dim] = sum(scores) / len(scores)

        # Weighted overall score
        weighted_sum = 0
        weight_total = 0
        for dim, score in aggregates.items():
            weight = weights.get(dim, 1.0)
            weighted_sum += score * weight
            weight_total += weight

        if weight_total > 0:
            aggregates["overall"] = weighted_sum / weight_total

        return aggregates

    def save_results(
        self,
        run: EvaluationRun,
        output_path: str | Path | None = None,
    ) -> Path:
        """Save evaluation results to JSON file."""
        if output_path is None:
            output_path = get_reports_dir() / f"eval_{run.run_id}.json"

        output_path = Path(output_path)

        # Convert to serializable format
        data = {
            "run_id": run.run_id,
            "agent_name": run.agent_name,
            "timestamp": run.timestamp,
            "config": run.config,
            "summary": {
                "total_scenarios": run.total_scenarios,
                "passed": run.passed_scenarios,
                "failed": run.failed_scenarios,
                "pass_rate": run.pass_rate,
                "aggregate_scores": run.aggregate_scores,
            },
            "results": [
                {
                    "scenario_id": r.scenario.id,
                    "category": r.scenario.category,
                    "prompt": r.scenario.prompt,
                    "response": r.response.response,
                    "latency_ms": r.response.latency_ms,
                    "passed": r.passed,
                    "failure_reasons": r.failure_reasons,
                    "violations": [
                        {
                            "rule": v.rule_name,
                            "message": v.message,
                            "severity": v.severity,
                        }
                        for v in r.rule_violations
                    ],
                    "scores": {
                        name: {
                            "score": s.score,
                            "reasoning": s.reasoning,
                        }
                        for name, s in r.scores.items()
                    },
                }
                for r in run.results
            ],
        }

        save_json(data, output_path)
        return output_path


def run_comparison(
    agents: dict[str, ModelClient],
    scenarios_path: str | Path,
    config_path: str | Path | None = None,
    system_prompt: str | None = None,
) -> dict[str, EvaluationRun]:
    """
    Run evaluation comparison across multiple agents.

    Args:
        agents: Dictionary mapping agent names to their clients
        scenarios_path: Path to test scenarios JSON
        config_path: Optional path to config YAML
        system_prompt: Optional system prompt to use

    Returns:
        Dictionary mapping agent names to their evaluation runs
    """
    results = {}

    for name, client in agents.items():
        evaluator = Evaluator(
            client=client,
            agent_name=name,
            config_path=config_path,
            scenarios_path=scenarios_path,
        )

        run = evaluator.run_evaluation(system_prompt=system_prompt)
        results[name] = run

        # Save individual results
        evaluator.save_results(run)

    return results
