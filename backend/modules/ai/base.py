"""Abstract base for all AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ── Response DTOs ──────────────────────────────────────────────────────────────


@dataclass
class AIFunctionCall:
    """A single tool/function call requested by the AI."""

    call_id: str
    name: str
    arguments: str  # raw JSON string


@dataclass
class AIResponse:
    """Normalised response from any AI provider."""

    response_id: str | None = None
    text: str | None = None
    function_calls: list[AIFunctionCall] = field(default_factory=list)


# ── Abstract provider ─────────────────────────────────────────────────────────


class AIProvider(ABC):
    """Contract that every AI provider must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name, e.g. 'openai', 'mock'."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return *True* if the provider can serve requests right now."""
        ...

    @abstractmethod
    async def chat_with_tools(
        self,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        previous_response_id: str | None = None,
    ) -> AIResponse:
        """Send a user message together with tool definitions."""
        ...

    @abstractmethod
    async def continue_with_tool_results(
        self,
        *,
        model: str,
        system_prompt: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        previous_response_id: str,
    ) -> AIResponse:
        """Continue after executing tool calls — feed results back."""
        ...

    @abstractmethod
    async def generate_structured_output(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        schema_name: str = "output",
    ) -> dict[str, Any]:
        """Generate a JSON response constrained to *json_schema*."""
        ...
