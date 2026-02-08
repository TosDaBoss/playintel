"""
Report generation for evaluation results.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evaluator import EvaluationRun, TestResult
from .utils import (
    ensure_dir,
    format_score,
    format_percentage,
    Colors,
    print_header,
    print_subheader,
    get_reports_dir,
    save_json,
    timestamp,
)


@dataclass
class ComparisonReport:
    """Report comparing multiple agents."""
    runs: dict[str, EvaluationRun]
    winner: str | None
    rankings: list[tuple[str, float]]
    dimension_comparisons: dict[str, dict[str, float]]


class Reporter:
    """
    Generates reports from evaluation results.
    Supports terminal output, JSON, and Markdown formats.
    """

    def __init__(self, output_dir: str | Path | None = None):
        self.output_dir = Path(output_dir) if output_dir else get_reports_dir()
        ensure_dir(self.output_dir)

    def print_summary(self, run: EvaluationRun) -> None:
        """Print evaluation summary to terminal."""
        print_header(f"Evaluation Results: {run.agent_name}")

        # Overall stats
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Scenarios: {run.total_scenarios}")
        print(f"   Passed: {Colors.green(str(run.passed_scenarios))}")
        print(f"   Failed: {Colors.red(str(run.failed_scenarios))}")
        print(f"   Pass Rate: {Colors.score_color(run.pass_rate * 5, 3.5)} "
              f"({format_percentage(run.pass_rate)})")

        # Aggregate scores
        print_subheader("Dimension Scores")
        for dim, score in run.aggregate_scores.items():
            if dim != "overall":
                print(f"   {dim.replace('_', ' ').title():.<25} "
                      f"{Colors.score_color(score)}")

        if "overall" in run.aggregate_scores:
            print(f"\n   {'Overall':.<25} "
                  f"{Colors.bold(Colors.score_color(run.aggregate_scores['overall']))}")

        # Failed tests
        failed_results = [r for r in run.results if not r.passed]
        if failed_results:
            print_subheader(f"Failed Tests ({len(failed_results)})")
            for result in failed_results[:10]:  # Show first 10
                print(f"\n   ❌ {result.scenario.id} ({result.scenario.category})")
                print(f"      Prompt: {result.scenario.prompt[:60]}...")
                for reason in result.failure_reasons[:3]:
                    print(f"      • {reason}")

            if len(failed_results) > 10:
                print(f"\n   ... and {len(failed_results) - 10} more failures")

        print()

    def print_comparison(self, runs: dict[str, EvaluationRun]) -> None:
        """Print comparison of multiple agents to terminal."""
        print_header("Agent Comparison Report")

        # Rank by overall score
        rankings = sorted(
            [(name, run.aggregate_scores.get("overall", 0))
             for name, run in runs.items()],
            key=lambda x: x[1],
            reverse=True
        )

        print("\n🏆 Rankings:")
        for i, (name, score) in enumerate(rankings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"   {medal} {i}. {name}: {Colors.score_color(score)}")

        # Dimension comparison
        print_subheader("Dimension Breakdown")

        dimensions = ["naturalness", "depth_per_token", "table_judgement",
                     "variability", "scenario_handling"]

        # Header row
        agent_names = list(runs.keys())
        header = f"   {'Dimension':<25}"
        for name in agent_names:
            header += f"{name[:12]:>12}"
        print(header)
        print("   " + "-" * (25 + 12 * len(agent_names)))

        # Dimension rows
        for dim in dimensions:
            row = f"   {dim.replace('_', ' ').title():<25}"
            scores = []
            for name in agent_names:
                score = runs[name].aggregate_scores.get(dim, 0)
                scores.append(score)

            max_score = max(scores) if scores else 0
            for score in scores:
                if score == max_score and max_score > 0:
                    row += f"{Colors.green(format_score(score)):>12}"
                else:
                    row += f"{format_score(score):>12}"
            print(row)

        # Pass rate comparison
        print_subheader("Pass Rates")
        for name, run in runs.items():
            bar_length = int(run.pass_rate * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            print(f"   {name:<15} [{bar}] {format_percentage(run.pass_rate)}")

        print()

    def generate_markdown_report(
        self,
        run: EvaluationRun,
        include_responses: bool = False,
    ) -> str:
        """Generate a Markdown report for an evaluation run."""
        lines = []

        lines.append(f"# Evaluation Report: {run.agent_name}")
        lines.append(f"\n**Run ID:** {run.run_id}")
        lines.append(f"**Timestamp:** {run.timestamp}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Scenarios | {run.total_scenarios} |")
        lines.append(f"| Passed | {run.passed_scenarios} |")
        lines.append(f"| Failed | {run.failed_scenarios} |")
        lines.append(f"| Pass Rate | {format_percentage(run.pass_rate)} |")
        lines.append("")

        # Dimension Scores
        lines.append("## Dimension Scores")
        lines.append("")
        lines.append("| Dimension | Score |")
        lines.append("|-----------|-------|")
        for dim, score in run.aggregate_scores.items():
            if dim != "overall":
                lines.append(f"| {dim.replace('_', ' ').title()} | {format_score(score)}/5.0 |")
        if "overall" in run.aggregate_scores:
            lines.append(f"| **Overall** | **{format_score(run.aggregate_scores['overall'])}/5.0** |")
        lines.append("")

        # Results by Category
        lines.append("## Results by Category")
        lines.append("")

        categories = {}
        for result in run.results:
            cat = result.scenario.category
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0, "results": []}
            if result.passed:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
            categories[cat]["results"].append(result)

        for cat, data in sorted(categories.items()):
            total = data["passed"] + data["failed"]
            rate = data["passed"] / total if total > 0 else 0
            lines.append(f"### {cat.title()}")
            lines.append(f"- Passed: {data['passed']}/{total} ({format_percentage(rate)})")
            lines.append("")

        # Failed Tests
        failed_results = [r for r in run.results if not r.passed]
        if failed_results:
            lines.append("## Failed Tests")
            lines.append("")

            for result in failed_results:
                lines.append(f"### {result.scenario.id}")
                lines.append(f"**Category:** {result.scenario.category}")
                lines.append(f"**Prompt:** {result.scenario.prompt}")
                lines.append("")
                lines.append("**Failure Reasons:**")
                for reason in result.failure_reasons:
                    lines.append(f"- {reason}")
                lines.append("")

                if result.rule_violations:
                    lines.append("**Rule Violations:**")
                    for v in result.rule_violations:
                        lines.append(f"- [{v.severity}] {v.rule_name}: {v.message}")
                    lines.append("")

                if include_responses:
                    lines.append("**Response:**")
                    lines.append("```")
                    lines.append(result.response.response)
                    lines.append("```")
                    lines.append("")

        # Improvement Suggestions
        lines.append("## Improvement Suggestions")
        lines.append("")
        suggestions = self._generate_suggestions(run)
        for suggestion in suggestions:
            lines.append(f"- {suggestion}")
        lines.append("")

        return "\n".join(lines)

    def generate_comparison_markdown(
        self,
        runs: dict[str, EvaluationRun],
    ) -> str:
        """Generate a Markdown comparison report."""
        lines = []

        lines.append("# Agent Comparison Report")
        lines.append(f"\n**Generated:** {timestamp()}")
        lines.append("")

        # Rankings
        rankings = sorted(
            [(name, run.aggregate_scores.get("overall", 0))
             for name, run in runs.items()],
            key=lambda x: x[1],
            reverse=True
        )

        lines.append("## Rankings")
        lines.append("")
        lines.append("| Rank | Agent | Overall Score | Pass Rate |")
        lines.append("|------|-------|---------------|-----------|")
        for i, (name, score) in enumerate(rankings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
            pass_rate = format_percentage(runs[name].pass_rate)
            lines.append(f"| {medal} {i} | {name} | {format_score(score)}/5.0 | {pass_rate} |")
        lines.append("")

        # Dimension Comparison
        lines.append("## Dimension Comparison")
        lines.append("")

        dimensions = ["naturalness", "depth_per_token", "table_judgement",
                     "variability", "scenario_handling"]

        header = "| Dimension |"
        separator = "|-----------|"
        for name in runs.keys():
            header += f" {name} |"
            separator += "--------|"
        lines.append(header)
        lines.append(separator)

        for dim in dimensions:
            row = f"| {dim.replace('_', ' ').title()} |"
            scores = {name: run.aggregate_scores.get(dim, 0)
                     for name, run in runs.items()}
            max_score = max(scores.values()) if scores else 0

            for name in runs.keys():
                score = scores[name]
                formatted = format_score(score)
                if score == max_score and max_score > 0:
                    formatted = f"**{formatted}**"
                row += f" {formatted} |"
            lines.append(row)
        lines.append("")

        # Strengths and Weaknesses
        lines.append("## Agent Analysis")
        lines.append("")

        for name, run in runs.items():
            lines.append(f"### {name}")
            lines.append("")

            # Find strengths (scores >= 4.0)
            strengths = [
                dim for dim, score in run.aggregate_scores.items()
                if score >= 4.0 and dim != "overall"
            ]
            if strengths:
                lines.append("**Strengths:**")
                for s in strengths:
                    lines.append(f"- {s.replace('_', ' ').title()}")
                lines.append("")

            # Find weaknesses (scores < 3.5)
            weaknesses = [
                dim for dim, score in run.aggregate_scores.items()
                if score < 3.5 and dim != "overall"
            ]
            if weaknesses:
                lines.append("**Areas for Improvement:**")
                for w in weaknesses:
                    lines.append(f"- {w.replace('_', ' ').title()}")
                lines.append("")

        return "\n".join(lines)

    def _generate_suggestions(self, run: EvaluationRun) -> list[str]:
        """Generate improvement suggestions based on results."""
        suggestions = []

        # Analyze aggregate scores
        scores = run.aggregate_scores

        if scores.get("naturalness", 5) < 3.5:
            suggestions.append(
                "**Naturalness**: Reduce formulaic openings and persona introductions. "
                "Start responses with direct answers to questions."
            )

        if scores.get("depth_per_token", 5) < 3.5:
            suggestions.append(
                "**Depth**: Increase information density. Provide specific data points, "
                "examples, and actionable insights rather than generic statements."
            )

        if scores.get("table_judgement", 5) < 3.5:
            suggestions.append(
                "**Table Usage**: Review when tables are appropriate. Use tables for "
                "comparative data (3+ items) but prefer prose for simple answers."
            )

        if scores.get("variability", 5) < 3.5:
            suggestions.append(
                "**Variability**: Diversify response structures and openings. "
                "Avoid starting every response the same way."
            )

        if scores.get("scenario_handling", 5) < 3.5:
            suggestions.append(
                "**Scenario Handling**: Improve handling of edge cases and data gaps. "
                "Reframe limitations as opportunities rather than blockers."
            )

        # Analyze rule violations
        violation_types = {}
        for result in run.results:
            for v in result.rule_violations:
                violation_types[v.rule_name] = violation_types.get(v.rule_name, 0) + 1

        if violation_types.get("persona_introduction", 0) > 0:
            suggestions.append(
                "**Remove Persona Introductions**: The agent is introducing itself. "
                "Remove phrases like 'I am an AI assistant' or 'As a helpful bot'."
            )

        if violation_types.get("blunt_disclaimer", 0) > 0:
            suggestions.append(
                "**Soften Data Disclaimers**: Replace blunt 'I don't have that data' "
                "with helpful alternatives like 'Based on available data...' or "
                "'For more specific info, you might check...'."
            )

        if violation_types.get("table_overuse", 0) > 0:
            suggestions.append(
                "**Reduce Table Usage**: Tables are being used too frequently. "
                "Reserve them for genuinely comparative data."
            )

        if violation_types.get("repetitive_openings", 0) > 0:
            suggestions.append(
                "**Vary Openings**: Responses start too similarly. "
                "Use different opening structures based on the query type."
            )

        if not suggestions:
            suggestions.append("Great job! The agent is performing well across all dimensions.")

        return suggestions

    def save_markdown_report(
        self,
        run: EvaluationRun,
        filename: str | None = None,
        include_responses: bool = False,
    ) -> Path:
        """Save Markdown report to file."""
        if filename is None:
            filename = f"report_{run.run_id}.md"

        filepath = self.output_dir / filename
        content = self.generate_markdown_report(run, include_responses)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def save_comparison_markdown(
        self,
        runs: dict[str, EvaluationRun],
        filename: str | None = None,
    ) -> Path:
        """Save comparison Markdown report to file."""
        if filename is None:
            filename = f"comparison_{timestamp()}.md"

        filepath = self.output_dir / filename
        content = self.generate_comparison_markdown(runs)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def export_json(
        self,
        run: EvaluationRun,
        filename: str | None = None,
    ) -> Path:
        """Export results as JSON."""
        if filename is None:
            filename = f"results_{run.run_id}.json"

        filepath = self.output_dir / filename

        data = {
            "run_id": run.run_id,
            "agent_name": run.agent_name,
            "timestamp": run.timestamp,
            "summary": {
                "total_scenarios": run.total_scenarios,
                "passed": run.passed_scenarios,
                "failed": run.failed_scenarios,
                "pass_rate": run.pass_rate,
            },
            "aggregate_scores": run.aggregate_scores,
            "results": [
                {
                    "scenario_id": r.scenario.id,
                    "category": r.scenario.category,
                    "prompt": r.scenario.prompt,
                    "passed": r.passed,
                    "failure_reasons": r.failure_reasons,
                    "scores": {k: {"score": v.score, "reasoning": v.reasoning}
                              for k, v in r.scores.items()},
                }
                for r in run.results
            ],
        }

        save_json(data, filepath)
        return filepath

    def export_ci_summary(self, run: EvaluationRun) -> dict[str, Any]:
        """
        Export CI-friendly summary for automated pipelines.
        Returns a dict suitable for GitHub Actions annotations or similar.
        """
        return {
            "success": run.pass_rate >= 0.8,  # 80% pass threshold for CI
            "pass_rate": run.pass_rate,
            "total": run.total_scenarios,
            "passed": run.passed_scenarios,
            "failed": run.failed_scenarios,
            "overall_score": run.aggregate_scores.get("overall", 0),
            "dimension_scores": {
                k: v for k, v in run.aggregate_scores.items()
                if k != "overall"
            },
            "failure_summary": [
                {
                    "id": r.scenario.id,
                    "reasons": r.failure_reasons[:2],
                }
                for r in run.results if not r.passed
            ][:5],  # Top 5 failures
        }


def generate_full_report(
    runs: dict[str, EvaluationRun] | EvaluationRun,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    """
    Generate all report formats for evaluation results.

    Returns paths to generated files.
    """
    reporter = Reporter(output_dir)
    generated = {}

    if isinstance(runs, EvaluationRun):
        # Single run
        run = runs
        reporter.print_summary(run)
        generated["markdown"] = reporter.save_markdown_report(run)
        generated["json"] = reporter.export_json(run)
    else:
        # Comparison
        reporter.print_comparison(runs)
        generated["comparison_markdown"] = reporter.save_comparison_markdown(runs)

        for name, run in runs.items():
            generated[f"{name}_markdown"] = reporter.save_markdown_report(run)
            generated[f"{name}_json"] = reporter.export_json(run)

    return generated
