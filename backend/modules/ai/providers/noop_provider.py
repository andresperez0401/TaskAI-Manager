"""Noop AI provider — used when AI is explicitly disabled."""

from __future__ import annotations

from typing import Any

from modules.ai.base import AIProvider, AIResponse
from modules.ai.exceptions import AIDisabledError


class NoopProvider(AIProvider):
    """Always reports that AI is **not available**.

    Every method raises ``AIDisabledError`` so callers fall through to their
    fallback logic in a predictable way.
    """

    @property
    def provider_name(self) -> str:
        return "noop"

    @property
    def is_available(self) -> bool:
        return False

    async def chat_with_tools(
        self,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        previous_response_id: str | None = None,
    ) -> AIResponse:
        raise AIDisabledError()

    async def continue_with_tool_results(
        self,
        *,
        model: str,
        system_prompt: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        previous_response_id: str,
    ) -> AIResponse:
        raise AIDisabledError()

    async def generate_structured_output(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        schema_name: str = "output",
    ) -> dict[str, Any]:
        raise AIDisabledError()
