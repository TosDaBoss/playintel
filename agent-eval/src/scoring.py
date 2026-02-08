"""
Scoring rubric implementation for agent evaluation.

Provides both rule-based scoring and LLM-as-judge scoring templates.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import re

from .rules import check_single_response, check_table_presence, RuleCheckResult


class ScoreDimension(Enum):
    """Dimensions for scoring responses."""
    NATURALNESS = "naturalness"
    DEPTH_PER_TOKEN = "depth_per_token"
    TABLE_JUDGEMENT = "table_judgement"
    VARIABILITY = "variability"
    SCENARIO_HANDLING = "scenario_handling"


@dataclass
class DimensionScore:
    """Score for a single dimension."""
    dimension: ScoreDimension
    score: float  # 0-5
    reasoning: str
    confidence: float = 0.7  # 0-1, how confident is this score
    evidence: list[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Result of evaluating a single response."""
    response: str
    prompt: str
    dimension_scores: dict[ScoreDimension, DimensionScore]
    overall_score: float
    passed: bool
    failure_reasons: list[str] = field(default_factory=list)


@dataclass
class ResponseScore:
    """Complete score for a single response."""
    prompt_id: str
    response: str
    dimension_scores: dict[ScoreDimension, DimensionScore]
    rule_check: RuleCheckResult
    overall_score: float  # Weighted average
    passed: bool

    @property
    def naturalness(self) -> float:
        return self.dimension_scores.get(ScoreDimension.NATURALNESS, DimensionScore(
            ScoreDimension.NATURALNESS, 0, 0, ""
        )).score

    @property
    def depth(self) -> float:
        return self.dimension_scores.get(ScoreDimension.DEPTH_PER_TOKEN, DimensionScore(
            ScoreDimension.DEPTH_PER_TOKEN, 0, 0, ""
        )).score


# Default weights for dimensions
DEFAULT_WEIGHTS = {
    ScoreDimension.NATURALNESS: 0.25,
    ScoreDimension.DEPTH_PER_TOKEN: 0.20,
    ScoreDimension.TABLE_JUDGEMENT: 0.20,
    ScoreDimension.VARIABILITY: 0.15,
    ScoreDimension.SCENARIO_HANDLING: 0.20,
}


# =============================================================================
# Rule-Based Scoring (Heuristic)
# =============================================================================

class HeuristicScorer:
    """
    Scores responses using rule-based heuristics.
    Fast and deterministic, but less nuanced than LLM scoring.
    """

    def __init__(self, weights: dict[ScoreDimension, float] | None = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def score_naturalness(self, response: str, rule_check: RuleCheckResult | dict) -> DimensionScore:
        """Score naturalness based on rule violations and text analysis."""
        score = 5.0
        evidence = []
        reasoning_parts = []

        # Handle both RuleCheckResult and dict format
        if isinstance(rule_check, dict):
            violations = rule_check.get("violations", [])
        else:
            violations = rule_check.violations

        # Deduct for rule violations
        for violation in violations:
            rule_name = violation.rule_name if hasattr(violation, 'rule_name') else violation.get('rule_name', '')
            matched = violation.matched_text if hasattr(violation, 'matched_text') else violation.get('matched_text', '')

            if rule_name == "persona_introduction":
                score -= 3.0
                evidence.append(f"Persona intro: '{matched}'")
                reasoning_parts.append("Contains persona self-introduction")
            elif rule_name == "blunt_disclaimer":
                score -= 1.5
                evidence.append(f"Blunt disclaimer: '{matched}'")
                reasoning_parts.append("Blunt data disclaimer")
            elif rule_name in ("filler_opening", "filler_phrases"):
                score -= 0.5
                evidence.append(f"Filler: '{matched}'")
                reasoning_parts.append("Filler opening phrase")

        # Check for natural conversational elements (positive)
        if re.search(r'\?$', response.strip()):
            score += 0.3
            evidence.append("Ends with question (engagement)")

        # Check for varied sentence structure
        sentences = re.split(r'[.!?]+', response)
        if len(sentences) >= 3:
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if lengths and max(lengths) - min(lengths) > 5:
                score += 0.2
                evidence.append("Varied sentence lengths")

        score = max(0, min(5, score))
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Natural conversational tone"

        return DimensionScore(
            dimension=ScoreDimension.NATURALNESS,
            score=score,
            confidence=0.7,
            reasoning=reasoning,
            evidence=evidence
        )

    def score_depth(self, response: str, prompt: str) -> DimensionScore:
        """Score depth-per-token based on content analysis."""
        score = 3.0  # Start at neutral
        evidence = []
        reasoning_parts = []

        words = response.split()
        word_count = len(words)

        # Check for specific data points (numbers, percentages)
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', response)
        data_density = len(numbers) / max(word_count, 1) * 100

        if data_density > 3:
            score += 1.0
            evidence.append(f"High data density: {len(numbers)} numbers in {word_count} words")
        elif data_density > 1.5:
            score += 0.5
            evidence.append(f"Moderate data density: {len(numbers)} numbers")

        # Check for actionable language
        action_patterns = [
            r"I'?d (?:recommend|suggest|lean toward)",
            r"(?:next|first) step",
            r"(?:consider|try|test)",
            r"worth (?:checking|noting|exploring)",
        ]
        action_matches = sum(1 for p in action_patterns if re.search(p, response, re.I))
        if action_matches >= 2:
            score += 0.8
            evidence.append("Strong actionable language")
            reasoning_parts.append("Provides actionable guidance")
        elif action_matches >= 1:
            score += 0.4
            evidence.append("Some actionable language")

        # Check for insight patterns (non-obvious observations)
        insight_patterns = [
            r"interesting(?:ly)?",
            r"pattern",
            r"trend",
            r"outperform",
            r"correlation",
            r"compared to",
            r"(?:better|worse) than",
        ]
        insight_matches = sum(1 for p in insight_patterns if re.search(p, response, re.I))
        if insight_matches >= 2:
            score += 0.7
            evidence.append("Contains analytical insights")
            reasoning_parts.append("Provides non-obvious insights")

        # Penalize fluff
        fluff_patterns = [
            r"hope this helps",
            r"let me know if",
            r"feel free to",
            r"don'?t hesitate",
        ]
        fluff_matches = sum(1 for p in fluff_patterns if re.search(p, response, re.I))
        if fluff_matches > 0:
            score -= 0.5 * fluff_matches
            evidence.append(f"Contains {fluff_matches} fluff phrases")
            reasoning_parts.append("Some filler content")

        # Penalize very short responses
        if word_count < 30:
            score -= 1.0
            evidence.append(f"Very short: {word_count} words")
            reasoning_parts.append("Too brief for depth")

        score = max(0, min(5, score))
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Adequate depth"

        return DimensionScore(
            dimension=ScoreDimension.DEPTH_PER_TOKEN,
            score=score,
            confidence=0.6,
            reasoning=reasoning,
            evidence=evidence
        )

    def score_table_judgement(
        self,
        response: str,
        prompt: str,
        expects_table: bool | None = None
    ) -> DimensionScore:
        """Score appropriateness of table usage."""
        has_table, table_count = check_table_presence(response)
        evidence = []
        reasoning_parts = []

        # Keywords suggesting table would be appropriate
        table_appropriate_keywords = [
            r"compare",
            r"top \d+",
            r"rank",
            r"list",
            r"breakdown",
            r"side.by.side",
            r"which (?:games?|titles?)",
            r"show me",
        ]
        prompt_wants_table = any(
            re.search(p, prompt, re.I) for p in table_appropriate_keywords
        )

        if expects_table is not None:
            # We have ground truth
            if expects_table and has_table:
                score = 5.0
                reasoning_parts.append("Correctly used table when expected")
            elif expects_table and not has_table:
                score = 2.0
                reasoning_parts.append("Should have used table but didn't")
            elif not expects_table and has_table:
                score = 2.5
                reasoning_parts.append("Used table when not needed")
            else:
                score = 5.0
                reasoning_parts.append("Correctly avoided table")
        else:
            # Infer from prompt
            if prompt_wants_table:
                score = 5.0 if has_table else 3.0
                if has_table:
                    reasoning_parts.append("Appropriately used table for comparison request")
                else:
                    reasoning_parts.append("Could have used table for comparison")
                    # Check if offered table
                    if re.search(r"want (?:me to|a) .*table", response, re.I):
                        score = 4.5
                        reasoning_parts.append("Offered table option")
            else:
                # No strong signal for table
                if has_table:
                    # Check if table is large (many rows)
                    rows = len(re.findall(r'\n\|', response))
                    if rows > 5:
                        score = 3.5
                        reasoning_parts.append("Table may be excessive for this query")
                    else:
                        score = 4.0
                        reasoning_parts.append("Small table acceptable")
                else:
                    score = 4.5
                    reasoning_parts.append("Appropriately used prose")

        evidence.append(f"Has table: {has_table}")
        if has_table:
            evidence.append(f"Table count: {table_count}")

        score = max(0, min(5, score))
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Appropriate format choice"

        return DimensionScore(
            dimension=ScoreDimension.TABLE_JUDGEMENT,
            score=score,
            confidence=0.75,
            reasoning=reasoning,
            evidence=evidence
        )

    def score_scenario_handling(
        self,
        response: str,
        prompt: str,
        has_data_gap: bool = False
    ) -> DimensionScore:
        """Score how well the response handles the scenario, especially data gaps."""
        score = 4.0  # Start at good
        evidence = []
        reasoning_parts = []

        # Check for data gap keywords in prompt
        gap_keywords = ["ccu", "playtime", "concurrent", "active players", "revenue", "sales"]
        prompt_has_gap_request = any(kw in prompt.lower() for kw in gap_keywords)

        if prompt_has_gap_request or has_data_gap:
            # Check if response handles gap gracefully
            graceful_patterns = [
                r"(?:best|closest) proxy",
                r"(?:we can |I'?d )(?:use|look at)",
                r"(?:review|owner) (?:data |numbers )?suggest",
                r"based on (?:available|related)",
                r"instead[,:]",
            ]

            blunt_patterns = [
                r"(?:don'?t|doesn'?t) have (?:that |this )?data",
                r"not available",
                r"can'?t (?:access|get)",
            ]

            has_graceful = any(re.search(p, response, re.I) for p in graceful_patterns)
            has_blunt = any(re.search(p, response, re.I) for p in blunt_patterns)

            if has_graceful and not has_blunt:
                score = 5.0
                reasoning_parts.append("Excellent data gap handling with smooth pivot")
                evidence.append("Uses proxy metrics naturally")
            elif has_graceful and has_blunt:
                score = 3.5
                reasoning_parts.append("Mentions limitation but provides alternative")
                evidence.append("Mixed handling - acknowledges gap but pivots")
            elif has_blunt:
                score = 2.0
                reasoning_parts.append("Blunt data limitation without good alternative")
                evidence.append("Says 'no data' without smooth pivot")
            else:
                score = 3.5
                reasoning_parts.append("Neutral handling of potential data gap")

        # Check if response addresses the core question
        if "?" in prompt:
            # It's a question - check if there's a clear answer
            if re.search(r'^\s*(?:Yes|No|The|Based|Looking|For|In|About)', response):
                score += 0.3
                evidence.append("Addresses question directly")

        # Check for follow-up engagement
        if response.strip().endswith("?"):
            score += 0.2
            evidence.append("Ends with clarifying question")

        score = max(0, min(5, score))
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard scenario handling"

        return DimensionScore(
            dimension=ScoreDimension.SCENARIO_HANDLING,
            score=score,
            confidence=0.65,
            reasoning=reasoning,
            evidence=evidence
        )

    def score_response(
        self,
        response: str,
        prompt: str,
        prompt_metadata: dict[str, Any] | None = None
    ) -> ResponseScore:
        """
        Score a single response across all dimensions.

        Args:
            response: The agent's response text
            prompt: The user's prompt
            prompt_metadata: Optional metadata (expects_table, has_data_gap, etc.)

        Returns:
            Complete ResponseScore
        """
        metadata = prompt_metadata or {}

        # Run rule checks first
        rule_check = check_single_response(response)

        # Score each dimension
        dimension_scores = {}

        dimension_scores[ScoreDimension.NATURALNESS] = self.score_naturalness(
            response, rule_check
        )

        dimension_scores[ScoreDimension.DEPTH_PER_TOKEN] = self.score_depth(
            response, prompt
        )

        dimension_scores[ScoreDimension.TABLE_JUDGEMENT] = self.score_table_judgement(
            response, prompt, metadata.get("expects_table")
        )

        dimension_scores[ScoreDimension.SCENARIO_HANDLING] = self.score_scenario_handling(
            response, prompt, metadata.get("has_data_gap", False)
        )

        # Variability is scored across responses, so give neutral here
        dimension_scores[ScoreDimension.VARIABILITY] = DimensionScore(
            dimension=ScoreDimension.VARIABILITY,
            score=3.5,  # Neutral, will be adjusted in aggregate
            confidence=0.3,
            reasoning="Scored in aggregate across responses",
            evidence=[]
        )

        # Calculate weighted average
        total_weight = sum(self.weights.values())
        weighted_sum = sum(
            self.weights[dim] * score.score
            for dim, score in dimension_scores.items()
        )
        overall_score = weighted_sum / total_weight

        # Apply rule penalty
        overall_score *= (1 - rule_check.score_penalty)

        # Determine pass/fail
        passed = overall_score >= 3.5 and not rule_check.has_hard_fail

        return ResponseScore(
            prompt_id=metadata.get("id", "unknown"),
            response=response,
            dimension_scores=dimension_scores,
            rule_check=rule_check,
            overall_score=overall_score,
            passed=passed
        )


# =============================================================================
# LLM-as-Judge Scoring
# =============================================================================

LLM_JUDGE_PROMPT = """You are evaluating a Steam analytics agent's response quality.

## Scoring Rubric (0-5 scale for each dimension)

### Naturalness
- 5: Reads like a knowledgeable colleague; no persona intros, no robotic phrases
- 3: Generally natural but some stiffness or formulaic elements
- 1: Contains persona introductions, "I am an expert...", or robotic disclaimers

### Depth-per-Token
- 5: Every sentence adds value; specific data points; actionable insights
- 3: Some useful info but also filler; generic advice
- 1: Mostly fluff; no specific data; unhelpful generalities

### Table Judgement
- 5: Table used perfectly (for comparisons/rankings) or correctly avoided
- 3: Table choice is debatable but not wrong
- 1: Unnecessary table or missing table when comparison needed

### Scenario Handling
- 5: If data gap exists, pivots smoothly with proxy; addresses core question
- 3: Acknowledges limitations adequately but could be smoother
- 1: Bluntly says "no data" or fails to address the question

## Prompt
{prompt}

## Response to Evaluate
{response}

## Your Evaluation
For each dimension, provide:
1. Score (0-5)
2. Brief reasoning (1 sentence)

Format your response as:
NATURALNESS: [score] - [reasoning]
DEPTH_PER_TOKEN: [score] - [reasoning]
TABLE_JUDGEMENT: [score] - [reasoning]
SCENARIO_HANDLING: [score] - [reasoning]
OVERALL: [weighted average]
"""


def parse_llm_judge_response(llm_response: str) -> dict[ScoreDimension, DimensionScore]:
    """Parse the LLM judge's response into dimension scores."""
    scores = {}

    patterns = {
        ScoreDimension.NATURALNESS: r"NATURALNESS:\s*(\d(?:\.\d)?)\s*-\s*(.+?)(?:\n|$)",
        ScoreDimension.DEPTH_PER_TOKEN: r"DEPTH_PER_TOKEN:\s*(\d(?:\.\d)?)\s*-\s*(.+?)(?:\n|$)",
        ScoreDimension.TABLE_JUDGEMENT: r"TABLE_JUDGEMENT:\s*(\d(?:\.\d)?)\s*-\s*(.+?)(?:\n|$)",
        ScoreDimension.SCENARIO_HANDLING: r"SCENARIO_HANDLING:\s*(\d(?:\.\d)?)\s*-\s*(.+?)(?:\n|$)",
    }

    for dimension, pattern in patterns.items():
        match = re.search(pattern, llm_response, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            reasoning = match.group(2).strip()
            scores[dimension] = DimensionScore(
                dimension=dimension,
                score=min(5, max(0, score)),
                confidence=0.8,
                reasoning=reasoning,
                evidence=["LLM judge evaluation"]
            )

    return scores


class LLMJudgeScorer:
    """
    Scores responses using an LLM as judge.
    More nuanced but requires API calls.
    """

    def __init__(self, judge_client, weights: dict[ScoreDimension, float] | None = None):
        """
        Initialize LLM judge scorer.

        Args:
            judge_client: ModelClient to use for judging
            weights: Optional custom weights for dimensions
        """
        from .clients import ModelClient
        self.judge: ModelClient = judge_client
        self.weights = weights or DEFAULT_WEIGHTS

    def score(self, response: str, prompt: str) -> EvaluationResult:
        """
        Score a response using the LLM judge.

        Args:
            response: The agent's response
            prompt: The user's prompt

        Returns:
            EvaluationResult with dimension scores
        """
        result = self.score_response(response, prompt)
        return EvaluationResult(
            response=response,
            prompt=prompt,
            dimension_scores=result.dimension_scores,
            overall_score=result.overall_score,
            passed=result.passed,
            failure_reasons=[] if result.passed else ["Failed LLM judge evaluation"],
        )

    def score_response(
        self,
        response: str,
        prompt: str,
        prompt_metadata: dict[str, Any] | None = None
    ) -> ResponseScore:
        """Score a response using the LLM judge."""
        metadata = prompt_metadata or {}

        # Build the judge prompt
        judge_prompt = LLM_JUDGE_PROMPT.format(prompt=prompt, response=response)

        # Get LLM evaluation
        llm_response = self.judge.generate(judge_prompt)

        # Parse scores
        dimension_scores = parse_llm_judge_response(llm_response)

        # Add variability placeholder
        dimension_scores[ScoreDimension.VARIABILITY] = DimensionScore(
            dimension=ScoreDimension.VARIABILITY,
            score=3.5,
            confidence=0.3,
            reasoning="Scored in aggregate",
            evidence=[]
        )

        # Also run rule checks for hard fails
        rule_check = check_single_response(response)

        # Calculate overall score
        total_weight = sum(self.weights.values())
        weighted_sum = sum(
            self.weights.get(dim, 0.2) * score.score
            for dim, score in dimension_scores.items()
        )
        overall_score = weighted_sum / total_weight

        # Apply rule penalty
        overall_score *= (1 - rule_check.score_penalty)

        passed = overall_score >= 3.5 and not rule_check.has_hard_fail

        return ResponseScore(
            prompt_id=metadata.get("id", "unknown"),
            response=response,
            dimension_scores=dimension_scores,
            rule_check=rule_check,
            overall_score=overall_score,
            passed=passed
        )


# =============================================================================
# Aggregate Scoring
# =============================================================================

def score_variability(responses: list[str]) -> DimensionScore:
    """
    Score variability across multiple responses.

    Checks for:
    - Diverse sentence structures
    - Varied openings
    - Different response patterns
    """
    if len(responses) < 3:
        return DimensionScore(
            dimension=ScoreDimension.VARIABILITY,
            score=3.5,
            confidence=0.3,
            reasoning="Not enough responses to assess variability",
            evidence=[]
        )

    score = 4.0
    evidence = []

    # Check opening diversity
    openings = []
    for r in responses:
        words = r.split()[:5]
        opening = ' '.join(words).lower()
        opening = re.sub(r'[^\w\s]', '', opening)
        openings.append(opening)

    from collections import Counter
    opening_counts = Counter(openings)
    unique_ratio = len(opening_counts) / len(responses)

    if unique_ratio > 0.8:
        score += 0.5
        evidence.append(f"High opening diversity: {unique_ratio:.0%} unique")
    elif unique_ratio < 0.5:
        score -= 1.0
        evidence.append(f"Low opening diversity: {unique_ratio:.0%} unique")

    # Check structure diversity (paragraph count, bullet usage, etc.)
    structures = []
    for r in responses:
        struct = []
        if '\n\n' in r:
            struct.append('multi_para')
        if re.search(r'^\s*[-*•]', r, re.M):
            struct.append('bullets')
        if re.search(r'\|.*\|', r):
            struct.append('table')
        if r.strip().endswith('?'):
            struct.append('question')
        structures.append(tuple(sorted(struct)) if struct else ('plain',))

    struct_counts = Counter(structures)
    struct_unique = len(struct_counts)

    if struct_unique >= 3:
        score += 0.5
        evidence.append(f"Good structural variety: {struct_unique} patterns")
    elif struct_unique == 1:
        score -= 0.5
        evidence.append("All responses have same structure")

    score = max(0, min(5, score))

    return DimensionScore(
        dimension=ScoreDimension.VARIABILITY,
        score=score,
        confidence=0.7,
        reasoning=f"Based on {len(responses)} responses",
        evidence=evidence
    )
