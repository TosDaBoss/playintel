"""
Tests for scoring functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scoring import (
    ScoreDimension,
    DimensionScore,
    HeuristicScorer,
    EvaluationResult,
)


class TestDimensionScore:
    """Tests for DimensionScore dataclass."""

    def test_creates_score(self):
        """Should create a dimension score."""
        score = DimensionScore(
            dimension=ScoreDimension.NATURALNESS,
            score=4.5,
            reasoning="Good natural flow"
        )
        assert score.dimension == ScoreDimension.NATURALNESS
        assert score.score == 4.5
        assert "natural" in score.reasoning.lower()

    def test_score_bounds(self):
        """Score can be any float (validation is in scorer)."""
        score = DimensionScore(
            dimension=ScoreDimension.DEPTH_PER_TOKEN,
            score=0.0,
            reasoning=""
        )
        assert score.score == 0.0

        score = DimensionScore(
            dimension=ScoreDimension.DEPTH_PER_TOKEN,
            score=5.0,
            reasoning=""
        )
        assert score.score == 5.0


class TestHeuristicScorer:
    """Tests for heuristic-based scoring."""

    @pytest.fixture
    def scorer(self):
        return HeuristicScorer()

    def test_naturalness_high_score_clean_response(self, scorer):
        """Clean response should score high on naturalness."""
        response = "The top selling indie games this month include Balatro and Lethal Company."
        rule_result = {"violations": [], "passed": True}

        score = scorer.score_naturalness(response, rule_result)

        assert score.dimension == ScoreDimension.NATURALNESS
        assert score.score >= 4.0

    def test_naturalness_low_score_with_violations(self, scorer):
        """Response with violations should score lower."""
        response = "I am an AI assistant. The top games are..."
        # Simulate violation
        from src.rules import RuleViolation
        rule_result = {
            "violations": [
                RuleViolation(
                    rule_name="persona_introduction",
                    message="Persona detected",
                    severity="error",
                    matched_text="I am an AI assistant"
                )
            ],
            "passed": False
        }

        score = scorer.score_naturalness(response, rule_result)

        assert score.score < 4.0

    def test_depth_high_score_detailed_response(self, scorer):
        """Detailed response should score high on depth."""
        response = """The roguelike genre shows 15% year-over-year growth.
        Key factors: procedural generation appeals to replayability-focused players,
        the average price point of £12.99 offers good value, and successful titles
        like Hades (95% positive) set high quality bars. Competition is moderate
        with 200 new releases annually, but top performers capture most revenue."""
        prompt = "How is the roguelike genre performing?"

        score = scorer.score_depth(response, prompt)

        assert score.dimension == ScoreDimension.DEPTH_PER_TOKEN
        assert score.score >= 3.5

    def test_depth_low_score_shallow_response(self, scorer):
        """Shallow response should score lower on depth."""
        response = "Roguelikes are doing okay. Some games sell well."
        prompt = "How is the roguelike genre performing?"

        score = scorer.score_depth(response, prompt)

        assert score.score < 3.5

    def test_table_judgement_good_when_expected(self, scorer):
        """Using table when expected should score well."""
        response = """| Game | Price | Reviews |
|------|-------|---------|
| Hades | £19.99 | 95% |
| Dead Cells | £21.99 | 94% |"""
        prompt = "Compare the top roguelikes"
        expects_table = True

        score = scorer.score_table_judgement(response, prompt, expects_table)

        assert score.dimension == ScoreDimension.TABLE_JUDGEMENT
        assert score.score >= 4.0

    def test_table_judgement_bad_when_not_needed(self, scorer):
        """Using table when not needed should score lower."""
        response = """| Answer |
|--------|
| 30 games daily |"""
        prompt = "How many games release on Steam daily?"
        expects_table = False

        score = scorer.score_table_judgement(response, prompt, expects_table)

        assert score.score < 4.0

    def test_table_judgement_good_no_table_when_not_needed(self, scorer):
        """Not using table when not needed should score well."""
        response = "Approximately 30 games release on Steam daily."
        prompt = "How many games release on Steam daily?"
        expects_table = False

        score = scorer.score_table_judgement(response, prompt, expects_table)

        assert score.score >= 4.0

    def test_scenario_handling_data_gap_good(self, scorer):
        """Good handling of data gap should score well."""
        response = """While exact revenue figures aren't public, we can estimate
        based on review counts. Hollow Knight has 200k+ reviews, suggesting
        millions in sales. Similar indie hits in this range typically see
        £10-20M in lifetime revenue."""
        prompt = "What's the revenue for Hollow Knight?"
        has_data_gap = True

        score = scorer.score_scenario_handling(response, prompt, has_data_gap)

        assert score.dimension == ScoreDimension.SCENARIO_HANDLING
        assert score.score >= 3.5

    def test_scenario_handling_data_gap_bad(self, scorer):
        """Poor handling of data gap should score lower."""
        response = "I don't have that data. You should check elsewhere."
        prompt = "What's the revenue for Hollow Knight?"
        has_data_gap = True

        score = scorer.score_scenario_handling(response, prompt, has_data_gap)

        assert score.score < 3.0


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_creates_result(self):
        """Should create evaluation result."""
        scores = {
            ScoreDimension.NATURALNESS: DimensionScore(
                ScoreDimension.NATURALNESS, 4.0, "Good"
            ),
            ScoreDimension.DEPTH_PER_TOKEN: DimensionScore(
                ScoreDimension.DEPTH_PER_TOKEN, 3.5, "Average"
            ),
        }
        result = EvaluationResult(
            response="Test response",
            prompt="Test prompt",
            dimension_scores=scores,
            overall_score=3.75,
            passed=True,
            failure_reasons=[],
        )

        assert result.passed is True
        assert result.overall_score == 3.75
        assert len(result.dimension_scores) == 2

    def test_result_with_failures(self):
        """Should create result with failures."""
        result = EvaluationResult(
            response="Test response",
            prompt="Test prompt",
            dimension_scores={},
            overall_score=2.0,
            passed=False,
            failure_reasons=["Low naturalness score"],
        )

        assert result.passed is False
        assert len(result.failure_reasons) == 1


class TestScoreDimension:
    """Tests for ScoreDimension enum."""

    def test_all_dimensions_exist(self):
        """All expected dimensions should exist."""
        dims = [d.value for d in ScoreDimension]
        assert "naturalness" in dims
        assert "depth_per_token" in dims
        assert "table_judgement" in dims
        assert "variability" in dims
        assert "scenario_handling" in dims

    def test_dimension_count(self):
        """Should have exactly 5 dimensions."""
        assert len(ScoreDimension) == 5
