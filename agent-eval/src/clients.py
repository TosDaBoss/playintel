"""
Model client interfaces and implementations.

Provides a unified interface for calling different LLM providers.
Includes stubs for testing and placeholder implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import random


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 500
    temperature: float = 0.7
    top_p: float = 0.95
    stop_sequences: list[str] | None = None


class ModelClient(ABC):
    """Abstract base class for model clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: dict[str, Any] | None = None,
        config: GenerationConfig | None = None
    ) -> str:
        """
        Generate a response to the given prompt.

        Args:
            prompt: The user's input/question
            system: Optional system prompt (policy instructions)
            context: Optional context dict (conversation history, metadata)
            config: Optional generation configuration

        Returns:
            The model's response as a string
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the client/model name for reporting."""
        pass


class DummyClient(ModelClient):
    """
    Dummy client for testing the harness.
    Returns varied template responses to simulate different behaviors.
    """

    def __init__(self, behavior: str = "balanced"):
        """
        Initialize dummy client.

        Args:
            behavior: One of "balanced", "persona_heavy", "table_heavy", "minimal"
        """
        self._behavior = behavior
        self._call_count = 0

    @property
    def name(self) -> str:
        return f"dummy_{self._behavior}"

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: dict[str, Any] | None = None,
        config: GenerationConfig | None = None
    ) -> str:
        self._call_count += 1

        if self._behavior == "persona_heavy":
            return self._persona_response(prompt)
        elif self._behavior == "table_heavy":
            return self._table_response(prompt)
        elif self._behavior == "minimal":
            return self._minimal_response(prompt)
        else:
            return self._balanced_response(prompt)

    def _balanced_response(self, prompt: str) -> str:
        """Generate a reasonably good response."""
        responses = [
            # Pattern A - Quick Answer
            "Roguelikes in the $15-20 range see the best conversion—about 18% hit 100k+ owners. "
            "The sweet spot is 8-12 hours of content with high replayability. "
            "Worth checking: games with 'Difficult' tag outperform by 15%.",

            # Pattern B - Analysis Frame
            "For 50k wishlists, you're looking at 6-9 months of consistent visibility. "
            "Three factors dominate: trailer hook strength (first 10 seconds), demo availability during festivals, "
            "and steady devlog cadence. Games hitting this target average 2 festival appearances. "
            "I'd prioritize a demo for Next Fest—it's the highest-conversion event we track.",

            # Pattern C - Options Layout
            "Two paths here. Premium pricing ($24.99+) works when you have 20+ hours and strong "
            "production values—success rate around 12% for indies. Value pricing ($9.99-14.99) "
            "is safer with 45% hitting 50k owners. Given your scope, I'd lean toward $14.99 launch "
            "with planned price increases after positive review momentum.",

            # Pattern D - Exploration
            "Interesting pattern in cozy survival: games combining relaxed pacing with light automation "
            "are outperforming pure survival by 2x on review scores. The 'Wholesome' tag correlation "
            "is strong—89% positive average vs 76% for broader survival. What's your core loop like?",
        ]
        return random.choice(responses)

    def _persona_response(self, prompt: str) -> str:
        """Generate a response with persona issues (for testing detection)."""
        return (
            "I am a Steam analytics expert with 8 years of experience in market research. "
            "The dataset doesn't have exact sales figures, but I can tell you that "
            "roguelikes generally perform well. The data provided doesn't have CCU information. "
            "Here's what I found:\n\n"
            "| Genre | Owners |\n|-------|--------|\n| Roguelike | 100k |\n| RPG | 200k |"
        )

    def _table_response(self, prompt: str) -> str:
        """Generate a response with excessive tables."""
        return (
            "Here's the breakdown:\n\n"
            "| Metric | Value |\n|--------|-------|\n"
            "| Avg Owners | 150k |\n| Median Price | $14.99 |\n| Review % | 85% |\n\n"
            "And by genre:\n\n"
            "| Genre | Count |\n|-------|-------|\n"
            "| Action | 5000 |\n| RPG | 3000 |\n| Indie | 8000 |"
        )

    def _minimal_response(self, prompt: str) -> str:
        """Generate a minimal/unhelpful response."""
        return "That looks fine. Let me know if you have other questions."


class OpenAIClientStub(ModelClient):
    """
    Stub for OpenAI API client.
    Replace with real implementation when API key is available.
    """

    def __init__(self, model: str = "gpt-4", api_key: str | None = None):
        self._model = model
        self._api_key = api_key

    @property
    def name(self) -> str:
        return f"openai_{self._model}"

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: dict[str, Any] | None = None,
        config: GenerationConfig | None = None
    ) -> str:
        # Stub implementation - replace with real API call
        if self._api_key is None:
            return self._stub_response(prompt)

        # Real implementation would be:
        # from openai import OpenAI
        # client = OpenAI(api_key=self._api_key)
        # messages = []
        # if system:
        #     messages.append({"role": "system", "content": system})
        # messages.append({"role": "user", "content": prompt})
        # response = client.chat.completions.create(
        #     model=self._model,
        #     messages=messages,
        #     max_tokens=config.max_tokens if config else 500
        # )
        # return response.choices[0].message.content

        raise NotImplementedError("Set OPENAI_API_KEY or implement real client")

    def _stub_response(self, prompt: str) -> str:
        """Return a stub response mimicking GPT behavior."""
        return (
            "Based on the Steam market data, roguelike games in the indie space show "
            "strong performance metrics. The median owner count for well-reviewed titles "
            "(85%+ positive) sits around 75,000, with top performers exceeding 500,000. "
            "Key success factors include: replayability depth, visual distinctiveness, "
            "and strategic pricing in the $12-18 range. Would you like me to break down "
            "specific comparables for your project?"
        )


class AnthropicClientStub(ModelClient):
    """
    Stub for Anthropic API client.
    Replace with real implementation when API key is available.
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        self._model = model
        self._api_key = api_key

    @property
    def name(self) -> str:
        return f"anthropic_{self._model.split('-')[1]}"

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: dict[str, Any] | None = None,
        config: GenerationConfig | None = None
    ) -> str:
        # Stub implementation - replace with real API call
        if self._api_key is None:
            return self._stub_response(prompt)

        # Real implementation would be:
        # import anthropic
        # client = anthropic.Anthropic(api_key=self._api_key)
        # message = client.messages.create(
        #     model=self._model,
        #     max_tokens=config.max_tokens if config else 500,
        #     system=system or "",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return message.content[0].text

        raise NotImplementedError("Set ANTHROPIC_API_KEY or implement real client")

    def _stub_response(self, prompt: str) -> str:
        """Return a stub response mimicking Claude behavior."""
        return (
            "Looking at the current Steam landscape, a few patterns stand out. "
            "Roguelikes continue their strong run, but the interesting opportunity "
            "is in hybrid genres—roguelike-deckbuilders and roguelike-autobattlers "
            "are seeing 30% better review-to-owner conversion than pure roguelikes. "
            "\n\nFor pricing, the $14.99 tier remains optimal for debuts. Games launching "
            "higher face a steeper visibility cliff unless they have existing audience. "
            "What's your target audience size? That'll help narrow the positioning."
        )


class CustomAgentClient(ModelClient):
    """
    Client for your custom Steam analytics agent.
    Wraps your agent's API or local inference.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        policy_file: str | None = None
    ):
        self._endpoint = endpoint
        self._policy = None
        if policy_file:
            with open(policy_file, 'r') as f:
                self._policy = f.read()

    @property
    def name(self) -> str:
        return "my_agent"

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: dict[str, Any] | None = None,
        config: GenerationConfig | None = None
    ) -> str:
        # Use policy file as system prompt if provided
        effective_system = system or self._policy

        if self._endpoint:
            # Call your agent's API
            # import requests
            # response = requests.post(
            #     self._endpoint,
            #     json={
            #         "prompt": prompt,
            #         "system": effective_system,
            #         "context": context
            #     }
            # )
            # return response.json()["response"]
            raise NotImplementedError("Set endpoint or implement local inference")

        # Fallback: use a placeholder
        return self._placeholder_response(prompt)

    def _placeholder_response(self, prompt: str) -> str:
        """Placeholder until real agent is connected."""
        return (
            "The roguelike market shows 1,847 active titles with 73% average positive rating. "
            "Top performers share three traits: distinct visual style, deep meta-progression, "
            "and runs under 45 minutes. For your price point question—$14.99 converts best "
            "for 8-12 hour games in this space. Next step: identify 3-5 closest comps by tag overlap."
        )


def get_client(client_type: str, **kwargs) -> ModelClient:
    """
    Factory function to create model clients.

    Args:
        client_type: One of "dummy", "openai", "anthropic", "my_agent"
        **kwargs: Additional arguments passed to client constructor

    Returns:
        Configured ModelClient instance
    """
    clients = {
        "dummy": DummyClient,
        "openai": OpenAIClientStub,
        "anthropic": AnthropicClientStub,
        "my_agent": CustomAgentClient,
    }

    if client_type not in clients:
        raise ValueError(f"Unknown client type: {client_type}. Available: {list(clients.keys())}")

    return clients[client_type](**kwargs)
