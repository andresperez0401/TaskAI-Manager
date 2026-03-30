import pytest

from modules.agent.tools import build_tool_handlers
from modules.summary.service import SummaryService
from modules.tasks.service import TaskService


@pytest.mark.asyncio
async def test_agent_tools_registry(session):
    task_service = TaskService(session)
    summary_service = SummaryService(session)
    handlers = build_tool_handlers(task_service, summary_service)

    expected = {
        "create_task",
        "list_tasks",
        "get_task",
        "update_task",
        "complete_task",
        "delete_task",
        "count_tasks",
        "complete_tasks_by_filter",
        "delete_completed_tasks",
        "get_urgent_task",
        "get_tasks_due_today",
        "get_tasks_due_this_week",
        "generate_today_summary_data",
    }
    assert expected.issubset(set(handlers.keys()))
