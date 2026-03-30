"""Generic OpenAI-compatible provider — uses the Chat Completions API.

Works with any provider that exposes an OpenAI-compatible ``/v1/chat/completions``
endpoint (e.g. Ollama, LM Studio, Together, Groq, vLLM, etc.).

Configure via ``AI_BASE_URL`` environment variable.
"""

from __future__ import annotations

import json
import logging
import uuid
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


class GenericOpenAICompatibleProvider(AIProvider):
    """Uses the standard **Chat Completions API** with a custom ``base_url``."""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 30):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "generic_openai_compatible"

    @property
    def is_available(self) -> bool:
        return True

    # ── Convert tool specs from Responses-API format → Chat Completions format

    @staticmethod
    def _convert_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []
        for t in tools:
            converted.append(
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {}),
                    },
                }
            )
        return converted

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
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self._call(model, messages, tools)

    async def continue_with_tool_results(
        self,
        *,
        model: str,
        system_prompt: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        previous_response_id: str,
    ) -> AIResponse:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        assistant_tool_calls: list[dict[str, Any]] = []
        for out in tool_outputs:
            call_id = out.get("call_id", "")
            name = out.get("name", "")
            arguments = out.get("arguments", "{}")
            if not call_id or not name:
                continue
            assistant_tool_calls.append(
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": arguments,
                    },
                }
            )

        if assistant_tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": assistant_tool_calls,
                }
            )

        for out in tool_outputs:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": out.get("call_id", ""),
                    "content": out.get("output", ""),
                }
            )

        logger.info("AI continue_with_tool_results with %s tool outputs", len(tool_outputs))
        return await self._call(model, messages, tools)

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
        messages = [
            {"role": "system", "content": system_prompt + "\nResponde **solo** en JSON."},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content or "{}"
            return json.loads(text)
        except (OpenAIError, APIError) as exc:
            raise self._translate(exc) from exc

    # ── internal ───────────────────────────────────────────────────────────

    async def _call(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AIResponse:
        try:
            chat_tools = self._convert_tools(tools)
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                tools=chat_tools if chat_tools else None,
            )
            choice = response.choices[0]
            msg = choice.message

            function_calls: list[AIFunctionCall] = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    function_calls.append(
                        AIFunctionCall(
                            call_id=tc.id or uuid.uuid4().hex,
                            name=tc.function.name,
                            arguments=tc.function.arguments,
                        )
                    )

            return AIResponse(
                response_id=response.id,
                text=msg.content if not function_calls else None,
                function_calls=function_calls,
            )
        except (OpenAIError, APIError) as exc:
            raise self._translate(exc) from exc

    def _translate(self, exc: Exception) -> AIProviderError:
        provider = self.provider_name
        logger.error("Generic-compatible provider error: %s", exc)
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
