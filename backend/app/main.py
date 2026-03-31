import logging

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import engine, get_db_session
from core.logger import configure_logging
from modules.agent.service import AgentService
from modules.ai.schemas import AIChatRequest
from modules.agent.router import router as agent_router
from modules.ai.router import router as ai_router
from modules.ai.service import AiService
from modules.summary.router import router as summary_router
from modules.tasks.router import router as tasks_router

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────
# Ensures that ALL unhandled errors (DB crashes, etc.) still produce a
# proper JSON response that the CORS middleware can decorate with headers.
# Without this, unhandled exceptions produce a bare "Internal Server Error"
# text response that lacks CORS headers, causing the browser to show
# "Failed to fetch" instead of the actual error message.


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please check backend logs."},
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
async def health_alias() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/ai/status")
async def ai_status() -> dict:
    """Check AI provider availability — useful for frontend degraded mode banner."""
    service = AiService()
    result = await service.health(probe=False)
    return {
        "ai_enabled": result.ai_enabled,
        "provider": result.provider,
        "available": result.provider_available,
        "model": result.model,
        "allow_fallback": result.allow_fallback,
        "configured": result.configured,
        "can_chat": result.can_chat,
        "error": result.error,
    }


@app.get("/ai/health")
async def ai_health_alias(probe: bool = True) -> dict:
    service = AiService()
    result = await service.health(probe=probe)
    return {
        "data": {
            "ai_enabled": result.ai_enabled,
            "provider": result.provider,
            "model": result.model,
            "configured": result.configured,
            "provider_available": result.provider_available,
            "can_chat": result.can_chat,
            "allow_fallback": result.allow_fallback,
            "error": result.error,
        },
        "meta": {},
    }


@app.get("/db/health")
async def db_health() -> dict:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:  # noqa: BLE001
        logger.error("Database health check failed: %s", exc)
        return {
            "status": "error",
            "database": "disconnected",
            "error": "DB connection failed. Check DATABASE_URL/DIRECT_DATABASE_URL.",
        }


@app.get("/api/db/health")
async def db_health_alias() -> dict:
    return await db_health()


@app.post("/ai/chat")
async def ai_chat_alias(
    payload: AIChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    service = AgentService(session)
    result = await service.chat(payload.message, payload.session_id)
    actions = [a.model_dump() for a in result.actions]

    tasks_changed: list[dict] = []
    for action in actions:
        tool_name = action.get("tool_name", "")
        result_obj = action.get("result", {})
        if isinstance(result_obj, dict) and isinstance(result_obj.get("task"), dict):
            task = result_obj["task"]
            if isinstance(task.get("id"), int):
                tasks_changed.append({"id": task["id"], "operation": tool_name})
        if tool_name == "delete_task" and isinstance(action.get("arguments", {}), dict):
            task_id = action["arguments"].get("task_id")
            if isinstance(task_id, int):
                tasks_changed.append({"id": task_id, "operation": "delete_task"})

    return {
        "data": {
            "success": result.success,
            "provider_available": result.provider_available,
            "fallback_mode": result.fallback_mode,
            "answer": result.answer,
            "actions": actions,
            "tasks_changed": tasks_changed,
            "history": [m.model_dump() for m in result.history],
            "error": result.error,
        },
        "meta": {},
    }


@app.delete("/ai/history", status_code=status.HTTP_204_NO_CONTENT)
async def ai_history_alias(
    session_id: str = "global",
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = AgentService(session)
    service.clear_history(session_id)


app.include_router(tasks_router)
app.include_router(summary_router)
app.include_router(agent_router)
app.include_router(ai_router)

logger.info(
    "App started — AI_ENABLED=%s  AI_PROVIDER=%s  model=%s",
    settings.ai_enabled,
    settings.ai_provider,
    settings.ai_model,
)
