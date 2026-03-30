from datetime import datetime

from pydantic import BaseModel

from modules.tasks.schemas import TaskResponse


class SummaryStats(BaseModel):
    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue_count: int
    due_today_count: int
    upcoming_count: int


class SummaryAnalysis(BaseModel):
    text: str
    source: str  # "ai" | "fallback"


class TodaySummaryResponse(BaseModel):
    generated_at: datetime
    stats: SummaryStats
    analysis: SummaryAnalysis
    overdue_tasks: list[TaskResponse] = []
    due_today_tasks: list[TaskResponse] = []
    due_this_week_tasks: list[TaskResponse] = []
