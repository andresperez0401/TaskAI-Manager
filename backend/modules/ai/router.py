from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from modules.agent.schemas import AgentChatResponse
from modules.agent.service import AgentService
from modules.ai.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIChatResponseData,
    AIHealthData,
    AIHealthResponse,
    AIProviderTestRequest,
    AIProviderTestResponse,
)
from modules.ai.service import AiService

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _extract_tasks_changed(actions: list[dict]) -> list[dict]:
    changed: list[dict] = []
    for action in actions:
        tool_name = action.get("tool_name", "")
        result = action.get("result", {})
        if isinstance(result, dict) and isinstance(result.get("task"), dict):
            task = result["task"]
            if isinstance(task.get("id"), int):
                changed.append({"id": task["id"], "operation": tool_name})
        if tool_name == "delete_task" and isinstance(action.get("arguments", {}), dict):
            task_id = action["arguments"].get("task_id")
            if isinstance(task_id, int):
                changed.append({"id": task_id, "operation": "delete_task"})
    return changed


@router.get("/health", response_model=AIHealthResponse)
async def ai_health(probe: bool = Query(default=True)) -> AIHealthResponse:
    service = AiService()
    result = await service.health(probe=probe)
    return AIHealthResponse(
        data=AIHealthData(
            ai_enabled=result.ai_enabled,
            provider=result.provider,
            model=result.model,
            configured=result.configured,
            provider_available=result.provider_available,
            can_chat=result.can_chat,
            allow_fallback=result.allow_fallback,
            error=result.error,
        )
    )


@router.post("/test", response_model=AIProviderTestResponse)
async def ai_test_provider(payload: AIProviderTestRequest) -> AIProviderTestResponse:
    service = AiService()
    result = await service.test_provider_chat(payload.message)
    return AIProviderTestResponse(data=result)


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    payload: AIChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AIChatResponse:
    service = AgentService(session)
    result: AgentChatResponse = await service.chat(payload.message, payload.session_id)
    actions = [a.model_dump() for a in result.actions]
    return AIChatResponse(
        data=AIChatResponseData(
            success=result.success,
            provider_available=result.provider_available,
            fallback_mode=result.fallback_mode,
            answer=result.answer,
            actions=actions,
            tasks_changed=_extract_tasks_changed(actions),
            history=[m.model_dump() for m in result.history],
            error=result.error,
        )
    )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def ai_clear_history(
    session_id: str = "global",
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = AgentService(session)
    service.clear_history(session_id)
