"""
Tests for rule-based failure detection.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rules import (
    check_persona_introduction,
    check_blunt_disclaimer,
    check_filler_phrases,
    check_table_overuse,
    check_repetitive_openings,
    RuleViolation,
)


class TestPersonaIntroduction:
    """Tests for persona introduction detection."""

    def test_detects_ai_assistant_intro(self):
        """Should detect 'I'm an gaming expert' pattern."""
        response = "I'm a gaming expert here to help you. The top selling games are..."
        violations = check_persona_introduction(response)
        assert len(violations) >= 1
        assert violations[0].rule_name == "persona_introduction"

    def test_detects_analyst_intro(self):
        """Should detect 'As a market analyst' pattern."""
        response = "As a market analyst, I'll provide information about Steam..."
        violations = check_persona_introduction(response)
        assert len(violations) >= 1

    def test_detects_years_experience(self):
        """Should detect experience-based personas."""
        response = "I've been analyzing games for 5 years. The market shows..."
        violations = check_persona_introduction(response)
        assert len(violations) >= 1

    def test_ignores_clean_response(self):
        """Should not flag clean responses."""
        response = "The top selling games on Steam right now include Baldur's Gate 3..."
        violations = check_persona_introduction(response)
        assert len(violations) == 0

    def test_ignores_ai_mentioned_in_context(self):
        """Should not flag AI mentioned in different context."""
        response = "AI-powered games have been trending. Games like..."
        violations = check_persona_introduction(response)
        assert len(violations) == 0


class TestBluntDisclaimer:
    """Tests for blunt data disclaimer detection."""

    def test_detects_dont_have_data(self):
        """Should detect 'data doesn't have' pattern."""
        response = "The data doesn't have that."
        violations = check_blunt_disclaimer(response)
        assert len(violations) >= 1
        assert violations[0].rule_name == "blunt_disclaimer"

    def test_detects_data_not_available(self):
        """Should detect 'data isn't available' pattern."""
        response = "That data isn't available."
        violations = check_blunt_disclaimer(response)
        assert len(violations) >= 1

    def test_detects_dataset_doesnt_have(self):
        """Should detect 'dataset doesn't have' pattern."""
        response = "The dataset doesn't have that."
        violations = check_blunt_disclaimer(response)
        assert len(violations) >= 1

    def test_ignores_soft_handling(self):
        """Should not flag soft data gap handling."""
        response = "Based on available data, similar games typically sell around..."
        violations = check_blunt_disclaimer(response)
        assert len(violations) == 0

    def test_ignores_long_explanation(self):
        """Should not flag when there's a longer explanation with pivot."""
        response = "The data doesn't have exact revenue but we can use review counts as a proxy to estimate sales which suggests strong performance."
        violations = check_blunt_disclaimer(response)
        assert len(violations) == 0


class TestFillerPhrases:
    """Tests for filler phrase detection."""

    def test_detects_great_question(self):
        """Should detect 'great question' filler."""
        response = "Great question! The roguelike genre has been..."
        violations = check_filler_phrases(response)
        assert len(violations) >= 1
        assert violations[0].rule_name == "filler_phrases"

    def test_detects_thats_interesting(self):
        """Should detect 'That's interesting' opener."""
        response = "That's a great question. The market shows..."
        violations = check_filler_phrases(response)
        assert len(violations) >= 1

    def test_detects_let_me_think(self):
        """Should detect 'Let me think' filler."""
        response = "Let me think about this. The pricing strategy..."
        violations = check_filler_phrases(response)
        assert len(violations) >= 1

    def test_ignores_direct_response(self):
        """Should not flag direct responses."""
        response = "The average price for roguelikes on Steam is £12.99."
        violations = check_filler_phrases(response)
        assert len(violations) == 0


class TestTableOveruse:
    """Tests for table overuse detection."""

    def test_detects_overuse(self):
        """Should detect when tables are used too frequently."""
        responses = [
            "Here's a table:\n| Game | Price |\n|------|-------|\n| A | $10 |",
            "| Name | Score |\n|------|-------|\n| B | 95% |",
            "| Title | Sales |\n|-------|-------|\n| C | 1000 |",
            "| Genre | Count |\n|-------|-------|\n| RPG | 50 |",
            "The market is growing steadily.",  # Only one without table
        ]
        violations = check_table_overuse(responses, threshold=0.4)
        assert len(violations) >= 1
        assert any(v.rule_name == "table_overuse" for v in violations)

    def test_passes_reasonable_usage(self):
        """Should pass when table usage is reasonable."""
        responses = [
            "Here's a table:\n| Game | Price |\n|------|-------|",
            "The roguelike genre is performing well.",
            "Pricing should be around £15.",
            "Competition is moderate.",
            "Release timing matters for visibility.",
        ]
        violations = check_table_overuse(responses, threshold=0.4)
        assert len(violations) == 0

    def test_empty_responses(self):
        """Should handle empty response list."""
        violations = check_table_overuse([], threshold=0.4)
        assert len(violations) == 0


class TestRepetitiveOpenings:
    """Tests for repetitive opening detection."""

    def test_detects_repetitive_openings(self):
        """Should detect when many responses start the same way."""
        # Need exactly identical first 10 words (normalized) to trigger
        # All these have identical first 10 words: "based on the steam data the roguelike genre shows strong"
        responses = [
            "Based on the Steam data, the roguelike genre shows strong growth with 15% increase.",
            "Based on the Steam data, the roguelike genre shows strong performance in Q2.",
            "Based on the Steam data, the roguelike genre shows strong sales numbers.",
            "Based on the Steam data, the roguelike genre shows strong player engagement.",
            "Based on the Steam data, the roguelike genre shows strong review scores.",
            "Something completely different here to break the pattern up.",
        ]
        violations = check_repetitive_openings(responses, threshold=0.2)
        # 5/6 = 83% share same first 10 words, well above 20% threshold
        assert len(violations) >= 1
        assert any(v.rule_name == "repetitive_openings" for v in violations)

    def test_passes_varied_openings(self):
        """Should pass when openings are varied."""
        responses = [
            "The roguelike genre is thriving.",
            "Survival games have seen steady growth.",
            "For pricing, consider the competition.",
            "Early access can be beneficial.",
            "Market trends suggest opportunity.",
        ]
        violations = check_repetitive_openings(responses, threshold=0.2)
        assert len(violations) == 0

    def test_handles_short_responses(self):
        """Should handle very short responses gracefully."""
        responses = ["Yes.", "No.", "Maybe."]
        violations = check_repetitive_openings(responses, threshold=0.2)
        # Should return empty list for < 5 responses
        assert isinstance(violations, list)
        assert len(violations) == 0


class TestRuleViolation:
    """Tests for RuleViolation dataclass."""

    def test_creates_error_severity(self):
        """Should create violation with error severity."""
        v = RuleViolation(
            rule_name="test_rule",
            message="Test violation",
            severity="error",
            matched_text="test",
        )
        assert v.severity == "error"
        assert v.rule_name == "test_rule"

    def test_creates_warning_severity(self):
        """Should create violation with warning severity."""
        v = RuleViolation(
            rule_name="test_rule",
            message="Test warning",
            severity="warning",
        )
        assert v.severity == "warning"
        assert v.matched_text is None
