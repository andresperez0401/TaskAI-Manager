import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from core.enums import TaskPriority, TaskStatus
from modules.summary.service import SummaryService
from modules.tasks.schemas import TaskCreate, TaskUpdate
from modules.tasks.service import TaskService

ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def _to_status(value: str | None) -> TaskStatus | None:
    return TaskStatus(value) if value else None


def _to_priority(value: str | None) -> TaskPriority | None:
    return TaskPriority(value) if value else None


def _to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def build_tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": "create_task",
            "description": "Create a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "due_date": {"type": ["string", "null"], "description": "ISO datetime"},
                },
                "required": ["title"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "list_tasks",
            "description": "List tasks with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "due_date_from": {"type": ["string", "null"]},
                    "due_date_to": {"type": ["string", "null"]},
                    "search": {"type": ["string", "null"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_task",
            "description": "Get a single task by id. Use ONLY when user asks to view/details, not to mutate.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "update_task",
            "description": "Update task fields (title/description/status/priority/due_date). Use when user asks to edit/change/update.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "due_date": {"type": ["string", "null"]},
                },
                "required": ["task_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "complete_task",
            "description": "Mark a task as completed by id. Use when user asks to complete/finish/done a task.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "delete_task",
            "description": "Delete a task by id. Use when user asks to remove/delete a task.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "count_tasks",
            "description": "Count tasks with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "complete_tasks_by_filter",
            "description": "Mark tasks as completed by status/priority filter",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "delete_completed_tasks",
            "description": "Delete all completed tasks",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_urgent_task",
            "description": "Get the most urgent pending task",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_tasks_due_today",
            "description": "Get all active tasks due today",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_tasks_due_this_week",
            "description": "Get all active tasks due this week",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "generate_today_summary_data",
            "description": "Generate structured summary data for today",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]


def build_tool_handlers(
    task_service: TaskService,
    summary_service: SummaryService,
) -> dict[str, ToolHandler]:
    async def create_task(args: dict[str, Any]) -> dict[str, Any]:
        payload = TaskCreate(
            title=args["title"],
            description=args.get("description"),
            status=_to_status(args.get("status")) or TaskStatus.PENDING,
            priority=_to_priority(args.get("priority")) or TaskPriority.MEDIUM,
            due_date=_to_datetime(args.get("due_date")),
        )
        created = await task_service.create_task(payload)
        return {"task": {"id": created.id, "title": created.title, "status": created.status.value}}

    async def list_tasks(args: dict[str, Any]) -> dict[str, Any]:
        tasks, total = await task_service.list_tasks(
            status=_to_status(args.get("status")),
            priority=_to_priority(args.get("priority")),
            due_date_from=_to_datetime(args.get("due_date_from")),
            due_date_to=_to_datetime(args.get("due_date_to")),
            search=args.get("search"),
        )
        return {
            "total": total,
            "items": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in tasks
            ],
        }

    async def get_task(args: dict[str, Any]) -> dict[str, Any]:
        t = await task_service.get_task(args["task_id"])
        return {
            "task": {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status.value,
                "priority": t.priority.value,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
        }

    async def update_task(args: dict[str, Any]) -> dict[str, Any]:
        payload = TaskUpdate(
            title=args.get("title"),
            description=args.get("description"),
            status=_to_status(args.get("status")),
            priority=_to_priority(args.get("priority")),
            due_date=_to_datetime(args.get("due_date")),
        )
        updated = await task_service.update_task(args["task_id"], payload)
        return {"task": {"id": updated.id, "title": updated.title, "status": updated.status.value}}

    async def delete_task(args: dict[str, Any]) -> dict[str, Any]:
        await task_service.delete_task(args["task_id"])
        return {"deleted": 1}

    async def complete_task(args: dict[str, Any]) -> dict[str, Any]:
        updated = await task_service.complete_task(args["task_id"])
        return {
            "task": {
                "id": updated.id,
                "title": updated.title,
                "status": updated.status.value,
                "completed_at": updated.completed_at.isoformat() if updated.completed_at else None,
            }
        }

    async def count_tasks(args: dict[str, Any]) -> dict[str, Any]:
        total = await task_service.count_tasks(
            status=_to_status(args.get("status")),
            priority=_to_priority(args.get("priority")),
        )
        return {"count": total}

    async def complete_tasks_by_filter(args: dict[str, Any]) -> dict[str, Any]:
        return await task_service.complete_tasks_by_filter(
            status=_to_status(args.get("status")),
            priority=_to_priority(args.get("priority")),
        )

    async def delete_completed_tasks(_: dict[str, Any]) -> dict[str, Any]:
        return await task_service.delete_completed_tasks()

    async def get_urgent_task(_: dict[str, Any]) -> dict[str, Any]:
        task = await task_service.get_urgent_task()
        if not task:
            return {"task": None}
        return {
            "task": {
                "id": task.id,
                "title": task.title,
                "priority": task.priority.value,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
        }

    async def get_tasks_due_today(_: dict[str, Any]) -> dict[str, Any]:
        data = await summary_service.generate_today_summary_data()
        return {"items": data.get("due_today_tasks", [])}

    async def get_tasks_due_this_week(_: dict[str, Any]) -> dict[str, Any]:
        data = await summary_service.generate_today_summary_data()
        return {"items": data.get("due_this_week_tasks", [])}

    async def generate_today_summary_data(_: dict[str, Any]) -> dict[str, Any]:
        return await summary_service.generate_today_summary_data()

    return {
        "create_task": create_task,
        "list_tasks": list_tasks,
        "get_task": get_task,
        "update_task": update_task,
        "complete_task": complete_task,
        "delete_task": delete_task,
        "count_tasks": count_tasks,
        "complete_tasks_by_filter": complete_tasks_by_filter,
        "delete_completed_tasks": delete_completed_tasks,
        "get_urgent_task": get_urgent_task,
        "get_tasks_due_today": get_tasks_due_today,
        "get_tasks_due_this_week": get_tasks_due_this_week,
        "generate_today_summary_data": generate_today_summary_data,
    }
