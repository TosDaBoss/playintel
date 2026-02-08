#!/usr/bin/env python3
"""
Main entry point for running agent evaluations.

Usage:
    python run_eval.py                          # Run with defaults
    python run_eval.py --agent my_agent         # Specify agent name
    python run_eval.py --config custom.yaml     # Custom config
    python run_eval.py --compare                # Compare multiple agents
    python run_eval.py --ci                     # CI mode (exit code on fail)
"""

import argparse
import sys
from pathlib import Path

from src.clients import DummyClient, CustomAgentClient
from src.evaluator import Evaluator, run_comparison
from src.reporter import Reporter, generate_full_report
from src.utils import load_yaml, get_project_root, Colors


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run agent evaluation benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_eval.py                    # Quick test with dummy agent
  python run_eval.py --agent playintel  # Test your agent
  python run_eval.py --compare          # Compare agents
  python run_eval.py --ci               # CI mode with exit codes
        """,
    )

    parser.add_argument(
        "--agent", "-a",
        default="dummy",
        help="Agent name (dummy, playintel, or custom)",
    )

    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to config YAML file",
    )

    parser.add_argument(
        "--scenarios", "-s",
        default=None,
        help="Path to scenarios JSON file",
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run comparison across multiple agents",
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with error code on failure",
    )

    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for reports",
    )

    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Filter by scenario categories",
    )

    parser.add_argument(
        "--max-scenarios", "-m",
        type=int,
        default=0,
        help="Maximum scenarios to run (0 = all)",
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API URL for custom agent",
    )

    return parser.parse_args()


def get_client(agent_name: str, api_url: str = None):
    """Get the appropriate client for an agent."""
    if agent_name == "dummy":
        return DummyClient()
    elif agent_name == "playintel" or agent_name == "custom":
        return CustomAgentClient(
            api_url=api_url or "http://localhost:8000",
            api_key=None,  # Add if needed
        )
    else:
        print(f"Unknown agent: {agent_name}, using dummy client")
        return DummyClient()


def filter_scenarios(evaluator: Evaluator, categories: list, max_count: int):
    """Filter scenarios based on criteria."""
    if categories:
        evaluator.scenarios = [
            s for s in evaluator.scenarios
            if s.category in categories
        ]

    if max_count > 0:
        evaluator.scenarios = evaluator.scenarios[:max_count]


def run_single_evaluation(args):
    """Run evaluation for a single agent."""
    root = get_project_root()

    # Determine paths
    config_path = args.config or root / "configs" / "eval_config.yaml"
    scenarios_path = args.scenarios or root / "prompts" / "test_scenarios.json"

    # Load config if exists
    config_path = Path(config_path)
    if not config_path.exists():
        config_path = None

    # Get client
    client = get_client(args.agent, args.api_url)

    print(f"\n{Colors.bold('Steam Analytics Agent Evaluation')}")
    print(f"{'=' * 40}")
    print(f"Agent: {Colors.blue(args.agent)}")
    print(f"Scenarios: {scenarios_path}")
    if config_path:
        print(f"Config: {config_path}")
    print()

    # Create evaluator
    evaluator = Evaluator(
        client=client,
        agent_name=args.agent,
        config_path=config_path,
        scenarios_path=scenarios_path,
    )

    # Apply filters
    filter_scenarios(evaluator, args.categories, args.max_scenarios)

    # Override parallel setting if specified
    if args.parallel:
        evaluator.config["execution"]["parallel"] = True

    print(f"Running {len(evaluator.scenarios)} test scenarios...")
    print()

    # Load system prompt from agent policy
    system_prompt = None
    policy_path = root / "agent_policy.md"
    if policy_path.exists():
        system_prompt = policy_path.read_text()

    # Run evaluation
    run = evaluator.run_evaluation(system_prompt=system_prompt)

    # Generate reports
    reporter = Reporter(args.output)
    reporter.print_summary(run)

    # Save reports
    md_path = reporter.save_markdown_report(run, include_responses=args.verbose)
    json_path = reporter.export_json(run)

    print(f"\n📄 Reports saved:")
    print(f"   Markdown: {md_path}")
    print(f"   JSON: {json_path}")

    # CI mode
    if args.ci:
        ci_summary = reporter.export_ci_summary(run)
        if not ci_summary["success"]:
            print(f"\n{Colors.red('CI FAILED')}: Pass rate {run.pass_rate:.1%} < 80%")
            sys.exit(1)
        else:
            print(f"\n{Colors.green('CI PASSED')}: Pass rate {run.pass_rate:.1%}")

    return run


def run_comparison_mode(args):
    """Run comparison across multiple agents."""
    root = get_project_root()

    scenarios_path = args.scenarios or root / "prompts" / "test_scenarios.json"
    config_path = args.config

    # Define agents to compare
    agents = {
        "dummy": DummyClient(),
        # Add more agents here as they become available:
        # "playintel": CustomAgentClient("http://localhost:8000"),
        # "openai": OpenAIClientStub(),
        # "anthropic": AnthropicClientStub(),
    }

    print(f"\n{Colors.bold('Agent Comparison Evaluation')}")
    print(f"{'=' * 40}")
    print(f"Agents: {', '.join(agents.keys())}")
    print(f"Scenarios: {scenarios_path}")
    print()

    # Run comparison
    results = run_comparison(
        agents=agents,
        scenarios_path=scenarios_path,
        config_path=config_path,
    )

    # Generate comparison report
    reporter = Reporter(args.output)
    reporter.print_comparison(results)

    md_path = reporter.save_comparison_markdown(results)
    print(f"\n📄 Comparison report: {md_path}")

    return results


def main():
    """Main entry point."""
    args = parse_args()

    try:
        if args.compare:
            run_comparison_mode(args)
        else:
            run_single_evaluation(args)

    except FileNotFoundError as e:
        print(f"{Colors.red('Error')}: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.red('Error')}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
