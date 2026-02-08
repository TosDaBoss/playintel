"""
Tests for the main evaluation engine.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluator import (
    Evaluator,
    TestScenario,
    AgentResponse,
    TestResult,
    EvaluationRun,
    run_comparison,
)
from src.clients import DummyClient, GenerationConfig
from src.scoring import ScoreDimension, DimensionScore


class TestTestScenario:
    """Tests for TestScenario dataclass."""

    def test_creates_basic_scenario(self):
        """Should create a basic test scenario."""
        scenario = TestScenario(
            id="test-001",
            category="pricing",
            prompt="What's the average price for roguelikes?",
        )
        assert scenario.id == "test-001"
        assert scenario.category == "pricing"
        assert scenario.expects_table is False
        assert scenario.has_data_gap is False

    def test_creates_scenario_with_flags(self):
        """Should create scenario with table/gap flags."""
        scenario = TestScenario(
            id="test-002",
            category="competitor_analysis",
            prompt="Compare top roguelikes",
            expects_table=True,
            has_data_gap=False,
            metadata={"difficulty": "hard"},
        )
        assert scenario.expects_table is True
        assert scenario.metadata["difficulty"] == "hard"


class TestDummyClient:
    """Tests for DummyClient used in testing."""

    def test_generates_response(self):
        """DummyClient should generate a response."""
        client = DummyClient()
        response = client.generate("What are the top games?")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_generates_varied_responses(self):
        """DummyClient should vary responses."""
        client = DummyClient()
        responses = set()
        for i in range(5):
            response = client.generate(f"Query {i}")
            responses.add(response[:50])  # First 50 chars
        # Should have some variety
        assert len(responses) >= 2


class TestEvaluator:
    """Tests for the main Evaluator class."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator with dummy client."""
        return Evaluator(
            client=DummyClient(),
            agent_name="test_agent",
        )

    @pytest.fixture
    def sample_scenarios(self):
        """Sample test scenarios."""
        return [
            TestScenario(
                id="price-001",
                category="pricing",
                prompt="What's the average price?",
            ),
            TestScenario(
                id="genre-001",
                category="genre",
                prompt="How are roguelikes doing?",
            ),
            TestScenario(
                id="compare-001",
                category="comparison",
                prompt="Compare survival and city builder",
                expects_table=True,
            ),
        ]

    def test_creates_evaluator(self, evaluator):
        """Should create evaluator instance."""
        assert evaluator.agent_name == "test_agent"
        assert evaluator.client is not None
        assert evaluator.config is not None

    def test_default_config(self, evaluator):
        """Should have default configuration."""
        assert "generation" in evaluator.config
        assert "scoring" in evaluator.config
        assert "rules" in evaluator.config
        assert evaluator.config["scoring"]["pass_threshold"] == 3.5

    def test_add_scenario(self, evaluator):
        """Should add scenarios."""
        scenario = TestScenario(
            id="test-001",
            category="test",
            prompt="Test prompt",
        )
        evaluator.add_scenario(scenario)
        assert len(evaluator.scenarios) == 1

    def test_add_scenarios_from_dict(self, evaluator):
        """Should add scenarios from dict format."""
        scenarios = [
            {"id": "dict-001", "category": "test", "prompt": "First prompt"},
            {"id": "dict-002", "category": "test", "prompt": "Second prompt"},
        ]
        evaluator.add_scenarios_from_dict(scenarios)
        assert len(evaluator.scenarios) == 2

    def test_run_single_test(self, evaluator):
        """Should run a single test."""
        scenario = TestScenario(
            id="single-001",
            category="test",
            prompt="What's Steam's cut?",
        )
        result = evaluator.run_single_test(scenario)

        assert isinstance(result, TestResult)
        assert result.scenario.id == "single-001"
        assert result.response.response != ""
        assert isinstance(result.passed, bool)

    def test_run_evaluation(self, evaluator, sample_scenarios):
        """Should run full evaluation."""
        evaluator.scenarios = sample_scenarios
        run = evaluator.run_evaluation()

        assert isinstance(run, EvaluationRun)
        assert run.agent_name == "test_agent"
        assert run.total_scenarios == 3
        assert len(run.results) == 3
        assert 0 <= run.pass_rate <= 1.0

    def test_evaluation_has_aggregate_scores(self, evaluator, sample_scenarios):
        """Evaluation should have aggregate scores."""
        evaluator.scenarios = sample_scenarios
        run = evaluator.run_evaluation()

        assert "naturalness" in run.aggregate_scores
        assert "depth_per_token" in run.aggregate_scores
        assert "overall" in run.aggregate_scores

    def test_evaluation_empty_scenarios_raises(self, evaluator):
        """Should raise error with no scenarios."""
        with pytest.raises(ValueError, match="No test scenarios"):
            evaluator.run_evaluation()

    def test_run_with_system_prompt(self, evaluator, sample_scenarios):
        """Should pass system prompt to client."""
        evaluator.scenarios = sample_scenarios[:1]
        run = evaluator.run_evaluation(
            system_prompt="You are a Steam analytics expert."
        )
        assert run.total_scenarios == 1


class TestEvaluationRun:
    """Tests for EvaluationRun dataclass."""

    def test_creates_run(self):
        """Should create evaluation run."""
        run = EvaluationRun(
            run_id="test_run_001",
            agent_name="test_agent",
            timestamp="20240101_120000",
            config={},
            results=[],
            aggregate_scores={"overall": 4.0},
            pass_rate=0.8,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=2,
        )
        assert run.pass_rate == 0.8
        assert run.total_scenarios == 10


class TestRunComparison:
    """Tests for multi-agent comparison."""

    def test_compares_multiple_agents(self, tmp_path):
        """Should compare multiple agents."""
        # Create simple scenario file
        scenarios_path = tmp_path / "scenarios.json"
        scenarios_path.write_text("""{
            "scenarios": [
                {"id": "test-001", "category": "test", "prompt": "Test?"}
            ]
        }""")

        agents = {
            "agent_a": DummyClient(),
            "agent_b": DummyClient(),
        }

        results = run_comparison(
            agents=agents,
            scenarios_path=scenarios_path,
        )

        assert "agent_a" in results
        assert "agent_b" in results
        assert isinstance(results["agent_a"], EvaluationRun)


class TestResultSerialization:
    """Tests for saving/loading results."""

    def test_save_results(self, tmp_path):
        """Should save results to JSON."""
        evaluator = Evaluator(
            client=DummyClient(),
            agent_name="test_agent",
        )
        evaluator.add_scenario(TestScenario(
            id="save-001",
            category="test",
            prompt="Test prompt",
        ))

        run = evaluator.run_evaluation()
        output_path = tmp_path / "results.json"
        saved_path = evaluator.save_results(run, output_path)

        assert saved_path.exists()
        import json
        with open(saved_path) as f:
            data = json.load(f)
        assert data["agent_name"] == "test_agent"
        assert "results" in data
