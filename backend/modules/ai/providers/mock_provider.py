"""Mock AI provider — returns deterministic responses for testing."""

from __future__ import annotations

import json
import uuid
from typing import Any

from modules.ai.base import AIFunctionCall, AIProvider, AIResponse


class MockProvider(AIProvider):
    """Returns predictable, hard-coded responses. Useful for unit/integration tests."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def is_available(self) -> bool:
        return True

    async def chat_with_tools(
        self,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        previous_response_id: str | None = None,
    ) -> AIResponse:
        # If user message contains "crear tarea" or "create task", simulate a tool call
        lower = user_message.lower()
        if "crear" in lower or "create" in lower:
            return AIResponse(
                response_id=uuid.uuid4().hex,
                text=None,
                function_calls=[
                    AIFunctionCall(
                        call_id=uuid.uuid4().hex,
                        name="create_task",
                        arguments=json.dumps({"title": f"[mock] {user_message[:50]}"}),
                    )
                ],
            )
        return AIResponse(
            response_id=uuid.uuid4().hex,
            text=f"[MockProvider] Recibí tu mensaje: {user_message[:100]}",
        )

    async def continue_with_tool_results(
        self,
        *,
        model: str,
        system_prompt: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        previous_response_id: str,
    ) -> AIResponse:
        return AIResponse(
            response_id=uuid.uuid4().hex,
            text="[MockProvider] He procesado los resultados de las herramientas.",
        )

    async def generate_structured_output(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        schema_name: str = "output",
    ) -> dict[str, Any]:
        return {
            "diagnosis": "[MockProvider] Análisis de prueba generado automáticamente.",
            "prioritization_suggestion": "Prioriza las tareas vencidas y de alta prioridad.",
        }
