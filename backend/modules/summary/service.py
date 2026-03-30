"""Summary service — ALWAYS returns structured stats, optionally enhanced by AI."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from core.enums import TaskStatus
from core.utils import utcnow, week_end
from modules.ai.exceptions import AIProviderError
from modules.ai.factory import get_ai_provider
from modules.summary.schemas import SummaryAnalysis, SummaryStats, TodaySummaryResponse
from modules.tasks.schemas import TaskResponse
from modules.tasks.service import TaskService

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service = TaskService(session)

    # ── Public ─────────────────────────────────────────────────────────────

    async def get_today_summary(self) -> TodaySummaryResponse:
        # Step 1: Structured stats — this NEVER fails (pure DB)
        stats, overdue, due_today, due_week = await self._compute_stats()

        # Step 2: AI analysis — graceful fallback if unavailable
        analysis = await self._build_analysis(stats)

        return TodaySummaryResponse(
            generated_at=utcnow(),
            stats=stats,
            analysis=analysis,
            overdue_tasks=overdue,
            due_today_tasks=due_today,
            due_this_week_tasks=due_week,
        )

    async def generate_today_summary_data(self) -> dict:
        """Lightweight version used by agent tools (no AI call)."""
        stats, overdue, due_today, due_week = await self._compute_stats()
        return {
            "stats": stats.model_dump(),
            "overdue_tasks": [t.model_dump(mode="json") for t in overdue],
            "due_today_tasks": [t.model_dump(mode="json") for t in due_today],
            "due_this_week_tasks": [t.model_dump(mode="json") for t in due_week],
        }

    # ── Stats computation (pure DB, no AI) ─────────────────────────────────

    async def _compute_stats(
        self,
    ) -> tuple[SummaryStats, list[TaskResponse], list[TaskResponse], list[TaskResponse]]:
        now = utcnow()
        today = now.date()
        week_limit = week_end(today)

        all_tasks, total = await self.task_service.list_tasks()
        task_stats = await self.task_service.task_stats()

        overdue = [
            TaskResponse.model_validate(t)
            for t in all_tasks
            if t.due_date and t.due_date.date() < today and t.status != TaskStatus.COMPLETED
        ]
        due_today = [
            TaskResponse.model_validate(t)
            for t in all_tasks
            if t.due_date and t.due_date.date() == today and t.status != TaskStatus.COMPLETED
        ]
        due_week = [
            TaskResponse.model_validate(t)
            for t in all_tasks
            if t.due_date
            and today <= t.due_date.date() <= week_limit
            and t.status != TaskStatus.COMPLETED
        ]

        stats = SummaryStats(
            total_tasks=total,
            by_status=task_stats.by_status,
            by_priority=task_stats.by_priority,
            overdue_count=len(overdue),
            due_today_count=len(due_today),
            upcoming_count=len(due_week),
        )
        return stats, overdue, due_today, due_week

    # ── AI analysis with fallback ──────────────────────────────────────────

    async def _build_analysis(self, stats: SummaryStats) -> SummaryAnalysis:
        provider = get_ai_provider()
        settings = get_settings()

        if not provider.is_available:
            logger.info("AI provider not available, using fallback analysis.")
            return self._fallback_analysis(stats)

        if not settings.ai_allow_fallback:
            # If fallback is disabled and provider fails, we still try AI
            pass

        try:
            prompt_data = json.dumps(stats.model_dump())
            result = await provider.generate_structured_output(
                model=settings.ai_model,
                system_prompt=(
                    "Eres un analista de productividad. Responde JSON con campos "
                    "diagnosis y prioritization_suggestion, ambos breves y accionables."
                ),
                user_prompt=json.dumps({
                    "objective": "Analizar estado de tareas del día y sugerir priorización clara",
                    "summary_data": stats.model_dump(),
                }),
                json_schema={
                    "type": "object",
                    "properties": {
                        "diagnosis": {"type": "string"},
                        "prioritization_suggestion": {"type": "string"},
                    },
                    "required": ["diagnosis", "prioritization_suggestion"],
                    "additionalProperties": False,
                },
                schema_name="daily_summary_analysis",
            )
            text = (
                result.get("diagnosis", "")
                + "\n\n💡 "
                + result.get("prioritization_suggestion", "")
            )
            return SummaryAnalysis(text=text.strip(), source="ai")

        except AIProviderError as exc:
            logger.warning("AI analysis failed (%s), using fallback: %s", type(exc).__name__, exc)
            return self._fallback_analysis(stats)

        except Exception as exc:
            logger.error("Unexpected error during AI analysis: %s", exc)
            return self._fallback_analysis(stats)

    # ── Local fallback heuristic ───────────────────────────────────────────

    @staticmethod
    def _fallback_analysis(stats: SummaryStats) -> SummaryAnalysis:
        parts: list[str] = []

        if stats.overdue_count > 0:
            parts.append(
                f"⚠️ Tienes {stats.overdue_count} tarea(s) vencida(s). Atiéndelas primero."
            )
        if stats.due_today_count > 0:
            parts.append(
                f"📅 {stats.due_today_count} tarea(s) vencen hoy."
            )

        high = stats.by_priority.get("high", 0)
        if high > 0:
            parts.append(f"🔴 {high} tarea(s) de prioridad alta pendientes.")

        pending = stats.by_status.get("pending", 0)
        in_progress = stats.by_status.get("in_progress", 0)
        if pending + in_progress > 0:
            parts.append(
                f"📋 Total activas: {pending} pendiente(s), {in_progress} en progreso."
            )

        if not parts:
            parts.append("✅ No hay tareas críticas. ¡Buen trabajo!")

        parts.append(
            "\n💡 Prioriza tareas vencidas y de prioridad alta, luego revisa las que vencen hoy."
        )

        return SummaryAnalysis(text="\n".join(parts), source="fallback")
