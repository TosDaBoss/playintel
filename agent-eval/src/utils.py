"""
Utility functions for the evaluation harness.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any


def load_yaml(path: str | Path) -> dict:
    """Load a YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_json(path: str | Path) -> dict | list:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Save data to a JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_token_estimate(text: str) -> int:
    """
    Rough estimate of token count.
    Assumes ~4 chars per token (rough average for English).
    """
    return len(text) // 4


def format_score(score: float, precision: int = 2) -> str:
    """Format a score for display."""
    return f"{score:.{precision}f}"


def format_percentage(value: float, precision: int = 1) -> str:
    """Format a value as percentage."""
    return f"{value * 100:.{precision}f}%"


def ensure_dir(path: str | Path) -> Path:
    """Ensure a directory exists, creating if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_project_root() -> Path:
    """Get the project root directory."""
    # Assumes this file is in src/
    return Path(__file__).parent.parent


def get_config_path() -> Path:
    """Get the default config file path."""
    return get_project_root() / "configs" / "eval_config.yaml"


def get_prompts_path() -> Path:
    """Get the default prompts file path."""
    return get_project_root() / "prompts" / "test_scenarios.json"


def get_reports_dir() -> Path:
    """Get the reports directory."""
    return ensure_dir(get_project_root() / "reports")


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.END}"

    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.END}"

    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.END}"

    @classmethod
    def blue(cls, text: str) -> str:
        return f"{cls.BLUE}{text}{cls.END}"

    @classmethod
    def bold(cls, text: str) -> str:
        return f"{cls.BOLD}{text}{cls.END}"

    @classmethod
    def score_color(cls, score: float, threshold: float = 3.5) -> str:
        """Color a score based on pass/fail threshold."""
        formatted = format_score(score)
        if score >= threshold + 1:
            return cls.green(formatted)
        elif score >= threshold:
            return cls.yellow(formatted)
        else:
            return cls.red(formatted)


def print_header(text: str, char: str = "=", width: int = 60) -> None:
    """Print a formatted header."""
    print()
    print(char * width)
    print(f" {text}")
    print(char * width)


def print_subheader(text: str, char: str = "-", width: int = 40) -> None:
    """Print a formatted subheader."""
    print()
    print(f"{text}")
    print(char * min(len(text), width))
