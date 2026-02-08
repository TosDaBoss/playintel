"""
Automatic fail condition checks and rule-based evaluation.

These rules detect obvious issues that should trigger automatic failures
or flags in the evaluation.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Severity(Enum):
    """Severity level for rule violations."""
    HARD_FAIL = "hard_fail"      # Immediate failure
    SOFT_FAIL = "soft_fail"      # Significant issue
    WARNING = "warning"          # Minor issue
    FLAG = "flag"                # Worth noting


@dataclass
class RuleViolation:
    """Represents a rule violation in a response."""
    rule_name: str
    message: str
    severity: str = "error"  # "error", "warning", "info"
    matched_text: str | None = None  # The matched text that triggered the violation
    position: int | None = None  # Position in text where violation occurred


@dataclass
class RuleCheckResult:
    """Result of checking all rules against a response."""
    passed: bool
    violations: list[RuleViolation]
    score_penalty: float  # Penalty to apply to overall score (0.0 - 1.0)

    @property
    def has_hard_fail(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    @property
    def has_soft_fail(self) -> bool:
        return any(v.severity in ("error", "warning") for v in self.violations)


# =============================================================================
# Rule Definitions
# =============================================================================

# Persona introduction patterns
PERSONA_PATTERNS = [
    r"I am (?:a|an) .{1,50}(?:years?|experience)",
    r"As (?:a|an) .{1,30}analyst",
    r"I'?ve been (?:working|analyzing) .{1,30}for \d+",
    r"With (?:my )?\d+ years",
    r"I'?m (?:a|an) .{1,30}expert",
    r"Let me introduce myself",
]

# Blunt data disclaimer patterns (bad)
DATA_DISCLAIMER_PATTERNS = [
    r"(?:the )?data(?:set)? doesn'?t have",
    r"(?:the )?data provided doesn'?t (?:have|include)",
    r"(?:I|we) don'?t have (?:access to |data (?:on|for))",
    r"(?:this|that) (?:data|information) (?:is|isn'?t) (?:not )?(?:available|included)",
    r"unfortunately,? (?:the )?data",
    r"I can'?t (?:access|find|get) (?:that|this|the) data",
]

# Acceptable data gap handling patterns (good)
DATA_PIVOT_PATTERNS = [
    r"(?:best|closest) proxy",
    r"(?:we can |I'd )(?:use|look at)",
    r"(?:review|owner|rating) (?:data |numbers )?suggest",
    r"based on (?:available|related)",
    r"(?:alternative|instead)[,:]",
]

# Filler/fluff patterns
FILLER_PATTERNS = [
    r"^(?:Great|Good|Excellent|Interesting) question[!.]?",
    r"^That'?s (?:a )?(?:great|good|interesting|important)",
    r"^Let me (?:think|explain|break (?:this|that) down)",
    r"^I'?d be happy to",
    r"^Absolutely[!,]",
    r"^Of course[!,]",
]

# Table detection
TABLE_PATTERN = r"\|.+\|[\r\n]+\|[-:| ]+\|"


def check_persona_introduction(response: str) -> list[RuleViolation]:
    """Check for persona self-introductions."""
    violations = []

    for pattern in PERSONA_PATTERNS:
        matches = re.finditer(pattern, response, re.IGNORECASE)
        for match in matches:
            violations.append(RuleViolation(
                rule_name="persona_introduction",
                message="Response contains persona self-introduction",
                severity="error",
                matched_text=match.group(),
                position=match.start()
            ))

    return violations


def check_blunt_disclaimer(response: str) -> list[RuleViolation]:
    """Check for blunt data disclaimers without natural pivots."""
    violations = []

    for pattern in DATA_DISCLAIMER_PATTERNS:
        matches = list(re.finditer(pattern, response, re.IGNORECASE))
        for match in matches:
            # Check if there's a natural pivot nearby (within 100 chars after)
            context_after = response[match.end():match.end() + 100]
            has_pivot = any(
                re.search(pivot, context_after, re.IGNORECASE)
                for pivot in DATA_PIVOT_PATTERNS
            )

            # Also check the full sentence length
            sentence_end = response.find('.', match.end())
            if sentence_end == -1:
                sentence_end = len(response)
            sentence = response[match.start():sentence_end]

            # If sentence is short and has no pivot, it's too blunt
            if len(sentence.split()) > 12 or has_pivot:
                # Acceptable - it's a longer explanation or has a pivot
                continue

            violations.append(RuleViolation(
                rule_name="blunt_disclaimer",
                message="Blunt data disclaimer without natural pivot",
                severity="error",
                matched_text=match.group(),
                position=match.start()
            ))

    return violations


def check_filler_opening(response: str) -> list[RuleViolation]:
    """Check for filler/fluff openings."""
    violations = []

    # Only check the first 50 characters
    opening = response[:50]

    for pattern in FILLER_PATTERNS:
        match = re.search(pattern, opening, re.IGNORECASE)
        if match:
            violations.append(RuleViolation(
                rule_name="filler_phrases",
                message="Response starts with filler phrase",
                severity="warning",
                matched_text=match.group(),
                position=0
            ))
            break  # Only flag once

    return violations


# Alias for backwards compatibility
def check_filler_phrases(response: str) -> list[RuleViolation]:
    """Alias for check_filler_opening."""
    return check_filler_opening(response)


def check_table_presence(response: str) -> tuple[bool, int]:
    """
    Check if response contains markdown tables.

    Returns:
        Tuple of (has_table, table_count)
    """
    tables = re.findall(TABLE_PATTERN, response)
    return len(tables) > 0, len(tables)


def check_response_length(response: str, min_words: int = 20, max_words: int = 300) -> list[RuleViolation]:
    """Check if response length is appropriate."""
    violations = []
    word_count = len(response.split())

    if word_count < min_words:
        violations.append(RuleViolation(
            rule_name="too_short",
            message=f"Response too short ({word_count} words, min {min_words})",
            severity="error",
            matched_text=None,
            position=None
        ))

    if word_count > max_words:
        violations.append(RuleViolation(
            rule_name="too_long",
            message=f"Response too long ({word_count} words, max {max_words})",
            severity="warning",
            matched_text=None,
            position=None
        ))

    return violations


def check_single_response(response: str) -> RuleCheckResult:
    """
    Run all rule checks on a single response.

    Args:
        response: The agent's response text

    Returns:
        RuleCheckResult with all violations found
    """
    all_violations = []

    # Run all checks
    all_violations.extend(check_persona_introduction(response))
    all_violations.extend(check_blunt_disclaimer(response))
    all_violations.extend(check_filler_opening(response))
    all_violations.extend(check_response_length(response))

    # Calculate score penalty
    penalty = 0.0
    for violation in all_violations:
        if violation.severity == "error":
            penalty += 0.5
        elif violation.severity == "warning":
            penalty += 0.1

    penalty = min(penalty, 1.0)  # Cap at 1.0

    # Determine if passed
    passed = not any(
        v.severity == "error"
        for v in all_violations
    )

    return RuleCheckResult(
        passed=passed,
        violations=all_violations,
        score_penalty=penalty
    )


# =============================================================================
# Aggregate Checks (across multiple responses)
# =============================================================================

@dataclass
class AggregateCheckResult:
    """Result of checking patterns across multiple responses."""
    flags: list[str]
    table_usage_ratio: float
    repetitive_openings_ratio: float
    passed: bool


def check_table_overuse(responses: list[str], threshold: float = 0.4) -> list[RuleViolation]:
    """
    Check if tables are used in too many responses.

    Args:
        responses: List of response texts
        threshold: Maximum acceptable ratio of responses with tables

    Returns:
        List of RuleViolation if overuse detected
    """
    if not responses:
        return []

    table_count = sum(1 for r in responses if check_table_presence(r)[0])
    ratio = table_count / len(responses)

    if ratio > threshold:
        return [RuleViolation(
            rule_name="table_overuse",
            message=f"Tables used in {ratio:.1%} of responses (threshold: {threshold:.0%})",
            severity="warning",
        )]
    return []


def check_repetitive_openings(responses: list[str], threshold: float = 0.2) -> list[RuleViolation]:
    """
    Check if responses have repetitive openings.

    Args:
        responses: List of response texts
        threshold: Maximum acceptable ratio of repeated openings

    Returns:
        List of RuleViolation if repetitive openings detected
    """
    if len(responses) < 5:
        return []

    # Get first 10 words of each response
    openings = []
    for r in responses:
        words = r.split()[:10]
        opening = ' '.join(words).lower()
        # Normalize: remove punctuation
        opening = re.sub(r'[^\w\s]', '', opening)
        openings.append(opening)

    # Count duplicates
    from collections import Counter
    counter = Counter(openings)
    max_repeat = max(counter.values())
    ratio = max_repeat / len(responses)

    if ratio > threshold:
        return [RuleViolation(
            rule_name="repetitive_openings",
            message=f"Same opening in {ratio:.1%} of responses (threshold: {threshold:.0%})",
            severity="warning",
        )]
    return []


def check_aggregate(responses: list[str]) -> AggregateCheckResult:
    """
    Run aggregate checks across multiple responses.

    Args:
        responses: List of response texts

    Returns:
        AggregateCheckResult with flags and metrics
    """
    flags = []

    # Check table overuse
    table_overuse, table_ratio = check_table_overuse(responses)
    if table_overuse:
        flags.append(f"Table overuse: {table_ratio:.1%} of responses contain tables (threshold: 40%)")

    # Check repetitive openings
    repetitive, opening_ratio = check_repetitive_openings(responses)
    if repetitive:
        flags.append(f"Repetitive openings: {opening_ratio:.1%} of responses share same opening (threshold: 20%)")

    return AggregateCheckResult(
        flags=flags,
        table_usage_ratio=table_ratio,
        repetitive_openings_ratio=opening_ratio,
        passed=len(flags) == 0
    )


# =============================================================================
# Utility Functions
# =============================================================================

def get_rule_summary() -> dict:
    """Get a summary of all rules for documentation."""
    return {
        "persona_introduction": {
            "description": "Detects self-introductions with credentials",
            "severity": "HARD_FAIL",
            "patterns": PERSONA_PATTERNS
        },
        "blunt_disclaimer": {
            "description": "Detects blunt 'no data' statements without pivots",
            "severity": "SOFT_FAIL",
            "patterns": DATA_DISCLAIMER_PATTERNS
        },
        "filler_opening": {
            "description": "Detects generic filler phrases at start",
            "severity": "WARNING",
            "patterns": FILLER_PATTERNS
        },
        "table_overuse": {
            "description": "Flags if >40% of responses contain tables",
            "severity": "FLAG",
            "threshold": 0.4
        },
        "repetitive_openings": {
            "description": "Flags if >20% of responses share same opening",
            "severity": "FLAG",
            "threshold": 0.2
        }
    }
