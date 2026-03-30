from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from modules.agent.schemas import AgentChatRequest, AgentChatResponse
from modules.agent.service import AgentService

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    payload: AgentChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AgentChatResponse:
    service = AgentService(session)
    return await service.chat(payload.message, payload.session_id)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_agent_history(
    session_id: str = "global",
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = AgentService(session)
    service.clear_history(session_id)
