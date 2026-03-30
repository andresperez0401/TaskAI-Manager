"""OpenAI provider — uses the Responses API (native OpenAI)."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import (
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    OpenAIError,
    RateLimitError,
)
from openai import AsyncOpenAI

from modules.ai.base import AIFunctionCall, AIProvider, AIResponse
from modules.ai.exceptions import (
    AIAuthenticationError,
    AIBillingError,
    AIConfigurationError,
    AIModelNotFoundError,
    AIProviderError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AITimeoutError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """Provider that talks to the **official OpenAI Responses API**."""

    def __init__(self, api_key: str, model: str, timeout: int = 30):
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._model = model
        self._timeout = timeout

    # ── meta ───────────────────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def is_available(self) -> bool:
        return True  # eagerly considered available; errors surface at call-time

    # ── tool-calling ───────────────────────────────────────────────────────

    async def chat_with_tools(
        self,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        previous_response_id: str | None = None,
    ) -> AIResponse:
        try:
            response = await self._client.responses.create(
                model=model,
                instructions=system_prompt,
                previous_response_id=previous_response_id,
                input=user_message,
                tools=tools,
            )
            return self._parse_response(response)
        except (OpenAIError, APIError) as exc:
            raise self._translate(exc) from exc

    async def continue_with_tool_results(
        self,
        *,
        model: str,
        system_prompt: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        previous_response_id: str,
    ) -> AIResponse:
        try:
            response = await self._client.responses.create(
                model=model,
                instructions=system_prompt,
                previous_response_id=previous_response_id,
                input=tool_outputs,
                tools=tools,
            )
            return self._parse_response(response)
        except (OpenAIError, APIError) as exc:
            raise self._translate(exc) from exc

    # ── structured output ──────────────────────────────────────────────────

    async def generate_structured_output(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        schema_name: str = "output",
    ) -> dict[str, Any]:
        try:
            response = await self._client.responses.create(
                model=model,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}],
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": json_schema,
                    }
                },
            )
            return json.loads(response.output_text)
        except (OpenAIError, APIError) as exc:
            raise self._translate(exc) from exc

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(response: Any) -> AIResponse:
        function_calls = [
            AIFunctionCall(
                call_id=item.call_id,
                name=item.name,
                arguments=item.arguments,
            )
            for item in response.output
            if item.type == "function_call"
        ]
        return AIResponse(
            response_id=response.id,
            text=response.output_text if not function_calls else None,
            function_calls=function_calls,
        )

    def _translate(self, exc: Exception) -> AIProviderError:
        provider = self.provider_name
        logger.error("OpenAI provider error: %s", exc)
        if isinstance(exc, APIStatusError):
            status = exc.status_code or 0
            if status in (401, 403):
                return AIAuthenticationError(str(exc), provider=provider)
            if status == 402:
                return AIBillingError(str(exc), provider=provider)
            if status == 404:
                return AIModelNotFoundError(str(exc), provider=provider)
            if status == 429:
                return AIRateLimitError(str(exc), provider=provider)
            if status in (400, 422):
                return AIConfigurationError(str(exc), provider=provider)
        if isinstance(exc, AuthenticationError):
            return AIAuthenticationError(str(exc), provider=provider)
        if isinstance(exc, RateLimitError):
            return AIRateLimitError(str(exc), provider=provider)
        if isinstance(exc, APITimeoutError):
            return AITimeoutError(str(exc), provider=provider)
        if isinstance(exc, NotFoundError):
            return AIModelNotFoundError(str(exc), provider=provider)
        return AIProviderUnavailableError(str(exc), provider=provider)
