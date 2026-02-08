# Steam Analytics Agent Evaluation Harness

A comprehensive test suite for benchmarking conversational quality of Steam analytics agents against reference models (ChatGPT 5.2, Claude Sonnet).

## Overview

This harness evaluates:
- **Naturalness**: No persona repetition, no robotic disclaimers
- **Depth-per-token**: Insights without fluff
- **Table Judgement**: Smart decisions about when to use tables
- **Variability**: Avoids repetitive templates
- **Scenario Handling**: Graceful pivots when data is missing

## Directory Structure

```
agent-eval/
├── README.md
├── requirements.txt
├── pyproject.toml
├── agent_policy.md          # Agent response policy prompt
├── src/
│   ├── __init__.py
│   ├── clients.py           # Model client interfaces
│   ├── evaluator.py         # Main evaluation engine
│   ├── scoring.py           # Scoring rubric implementation
│   ├── rules.py             # Automatic fail condition checks
│   ├── reporter.py          # Report generation
│   └── utils.py             # Utilities
├── tests/
│   ├── __init__.py
│   ├── test_prompts.py      # Test prompt definitions
│   ├── test_rules.py        # Unit tests for rule checks
│   └── test_scoring.py      # Unit tests for scoring
├── prompts/
│   └── test_scenarios.json  # 30+ test scenarios
├── configs/
│   └── eval_config.yaml     # Configuration
└── reports/
    └── .gitkeep             # Generated reports go here
```

## Installation

```bash
cd agent-eval
pip install -e .
# or
pip install -r requirements.txt
```

## Quick Start

### Run Full Evaluation

```bash
# Run evaluation with dummy client (for testing the harness)
python -m src.evaluator --client dummy

# Run with specific model
python -m src.evaluator --client my_agent --policy agent_policy.md

# Compare multiple candidates
python -m src.evaluator --compare my_agent,chatgpt,claude
```

### Run Specific Tests

```bash
# Run pytest suite
pytest tests/ -v

# Run specific scenario
python -m src.evaluator --scenario genre_opportunity
```

### Generate Reports

```bash
# Generate full report
python -m src.reporter --input reports/latest_run.json --output reports/analysis.html

# Quick summary
python -m src.reporter --input reports/latest_run.json --summary
```

## Configuration

Edit `configs/eval_config.yaml`:

```yaml
candidates:
  my_agent:
    type: "custom"
    policy_file: "agent_policy.md"
  chatgpt:
    type: "openai_stub"
  claude:
    type: "anthropic_stub"

scoring:
  weights:
    naturalness: 0.25
    depth_per_token: 0.20
    table_judgement: 0.20
    variability: 0.15
    scenario_handling: 0.20

thresholds:
  pass: 3.5
  excellent: 4.5
```

## Scoring Rubric

Each response is scored on 5 dimensions (0-5 scale):

| Dimension | 0-1 | 2-3 | 4-5 |
|-----------|-----|-----|-----|
| **Naturalness** | Persona intros, robotic | Some stiffness | Human analyst voice |
| **Depth-per-token** | Generic/fluff | Basic insights | Sharp, actionable |
| **Table Judgement** | Tables everywhere | Sometimes off | Perfect fit |
| **Variability** | Cookie-cutter | Some variation | Fresh structures |
| **Scenario Handling** | "No data" errors | Okay pivots | Seamless adaptation |

## Automatic Fail Conditions

The harness flags responses that:

1. **Persona Introduction**: Contains "I am a/an ... years/experience"
2. **Blunt Data Disclaimer**: Says "dataset doesn't have" without natural pivot
3. **Table Overuse**: Tables in >40% of responses
4. **Repetitive Openings**: Same first 10 words in >20% of responses

## Adding Custom Model Clients

Implement the `ModelClient` interface:

```python
from src.clients import ModelClient

class MyModelClient(ModelClient):
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: dict | None = None
    ) -> str:
        # Your implementation
        return response
```

## CI Integration

```yaml
# .github/workflows/eval.yml
name: Agent Evaluation
on: [push, pull_request]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: python -m src.evaluator --client my_agent --output reports/ci_run.json
      - run: python -m src.reporter --input reports/ci_run.json --ci-check --threshold 3.5
```

## License

MIT
