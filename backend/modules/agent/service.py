"""Agent service — uses AI provider abstraction with graceful degradation."""

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from modules.agent.memory import agent_memory
from modules.agent.schemas import AgentAction, AgentChatResponse
from modules.agent.tools import build_tool_handlers, build_tool_specs
from modules.ai.base import AIResponse
from modules.ai.exceptions import AIProviderError
from modules.ai.factory import get_ai_provider
from modules.ai.service import AiService
from modules.summary.service import SummaryService
from modules.tasks.service import TaskService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a task management AI agent.
Rules:
- Use tools whenever user asks to create, update, delete, count, summarize or query real tasks.
- If the user asks to update/complete/delete a task by id, you MUST call the corresponding tool.
- Do not stop at reading a task when the user explicitly requested a mutation.
- Tool routing policy:
    - "create/new" -> create_task
    - "list/show" -> list_tasks
    - "details" -> get_task
    - "update/change/edit" -> update_task
    - "complete/done/finish" -> complete_task
    - "delete/remove" -> delete_task
- If user provides enough fields for an update (e.g. task id + one field), execute update_task immediately.
- Do not ask follow-up questions when required fields for the chosen tool are already present.
- Keep responses concise and actionable.
- If tool output is enough, explain what was done.
- Never invent IDs or task data.
""".strip()


class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.provider = get_ai_provider()

    # ── Main chat entry ────────────────────────────────────────────────────

    async def chat(self, message: str, session_id: str = "global") -> AgentChatResponse:
        logger.info("Agent chat request received (session_id=%s)", session_id)
        # Check provider availability
        if not self.provider.is_available:
            logger.info("AI provider not available, returning fallback response.")
            return self._unavailable_response(message, session_id)

        agent_memory.append(session_id, "user", message)

        try:
            answer, actions = await self._run_with_tools(message, session_id)
        except AIProviderError as exc:
            mapped = AiService.classify_error(exc)
            logger.warning(
                "AI provider error during chat (%s): %s", mapped["code"], exc
            )
            answer = f"{mapped['message']} El CRUD de tareas sigue operativo desde la sección de Tareas."
            actions = []
            agent_memory.append(session_id, "assistant", answer)
            return AgentChatResponse(
                success=False,
                provider_available=False,
                fallback_mode=True,
                answer=answer,
                message=answer,
                actions=actions,
                history=agent_memory.get(session_id).history,
                error=mapped,
            )
        except Exception as exc:
            logger.error("Unexpected error in agent chat: %s", exc)
            answer = (
                "Ocurrió un error inesperado. El CRUD de tareas sigue disponible "
                "desde la sección de Tareas."
            )
            actions = []
            agent_memory.append(session_id, "assistant", answer)
            return AgentChatResponse(
                success=False,
                provider_available=False,
                fallback_mode=True,
                answer=answer,
                message=answer,
                actions=actions,
                history=agent_memory.get(session_id).history,
                error={"code": "INTERNAL_ERROR", "message": answer},
            )

        agent_memory.append(session_id, "assistant", answer)
        return AgentChatResponse(
            success=True,
            provider_available=True,
            fallback_mode=False,
            answer=answer,
            actions=actions,
            history=agent_memory.get(session_id).history,
        )

    # ── Tool calling loop ──────────────────────────────────────────────────

    async def _run_with_tools(
        self, message: str, session_id: str
    ) -> tuple[str, list[AgentAction]]:
        task_service = TaskService(self.session)
        summary_service = SummaryService(self.session)
        tool_specs = build_tool_specs()
        handlers = build_tool_handlers(task_service, summary_service)

        state = agent_memory.get(session_id)
        model = self.settings.ai_model

        response: AIResponse = await self.provider.chat_with_tools(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            user_message=message,
            tools=tool_specs,
            previous_response_id=state.previous_response_id,
        )

        actions: list[AgentAction] = []

        while True:
            if not response.function_calls:
                break

            outputs = []
            for call in response.function_calls:
                args: dict[str, Any] = json.loads(call.arguments)
                handler = handlers.get(call.name)
                if handler is None:
                    logger.warning("Unknown tool call: %s", call.name)
                    result = {"error": f"Unknown tool: {call.name}"}
                else:
                    try:
                        result = await handler(args)
                    except Exception as tool_exc:  # noqa: BLE001
                        logger.warning(
                            "Tool execution failed (%s): %s", call.name, tool_exc
                        )
                        result = {
                            "error": str(tool_exc),
                            "tool": call.name,
                        }
                logger.info("Agent executed tool=%s args=%s", call.name, args)
                actions.append(
                    AgentAction(tool_name=call.name, arguments=args, result=result)
                )
                outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "name": call.name,
                        "arguments": call.arguments,
                        "output": json.dumps(result),
                    }
                )

            try:
                response = await self.provider.continue_with_tool_results(
                    model=model,
                    system_prompt=SYSTEM_PROMPT,
                    tool_outputs=outputs,
                    tools=tool_specs,
                    previous_response_id=response.response_id or "",
                )
            except AIProviderError as exc:
                logger.warning(
                    "Provider failed after tool execution (%s): %s",
                    type(exc).__name__,
                    exc,
                )
                if actions:
                    response = AIResponse(
                        response_id=response.response_id,
                        text=(
                            "Ejecuté las acciones solicitadas sobre tus tareas, "
                            "pero no pude completar el texto final con el proveedor IA."
                        ),
                        function_calls=[],
                    )
                else:
                    raise
                break

        agent_memory.set_previous_response_id(session_id, response.response_id)
        answer = response.text or "He procesado tu solicitud."
        return answer, actions

    # ── Fallback when provider is unavailable ──────────────────────────────

    def _unavailable_response(
        self, message: str, session_id: str
    ) -> AgentChatResponse:
        fallback_answer = (
            "El proveedor de IA no está disponible en este momento. "
            "El CRUD de tareas sigue operativo desde la sección de Tareas."
        )
        agent_memory.append(session_id, "user", message)
        agent_memory.append(session_id, "assistant", fallback_answer)
        return AgentChatResponse(
            success=False,
            provider_available=False,
            fallback_mode=True,
            answer=fallback_answer,
            message=fallback_answer,
            actions=[],
            history=agent_memory.get(session_id).history,
            data=None,
            error={
                "code": "AI_PROVIDER_UNAVAILABLE",
                "message": "El proveedor de IA no está disponible en este momento.",
            },
        )

    # ── History management (works regardless of AI) ────────────────────────

    def clear_history(self, session_id: str = "global") -> None:
        agent_memory.clear(session_id)
