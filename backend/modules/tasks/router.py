from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from core.enums import TaskPriority, TaskStatus
from modules.tasks.schemas import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    TaskUpdate,
)
from modules.tasks.service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    service = TaskService(session)
    task = await service.create_task(payload)
    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: TaskStatus | None = Query(default=None),
    priority: TaskPriority | None = Query(default=None),
    due_date_from: datetime | None = Query(default=None),
    due_date_to: datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> TaskListResponse:
    service = TaskService(session)
    items, total = await service.list_tasks(
        status=status,
        priority=priority,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        search=search,
    )
    return TaskListResponse(items=[TaskResponse.model_validate(x) for x in items], total=total)


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(session: AsyncSession = Depends(get_db_session)) -> TaskStatsResponse:
    service = TaskService(session)
    return await service.task_stats()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, session: AsyncSession = Depends(get_db_session)) -> TaskResponse:
    service = TaskService(session)
    task = await service.get_task(task_id)
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    service = TaskService(session)
    task = await service.update_task(task_id, payload)
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    service = TaskService(session)
    task = await service.complete_task(task_id)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_db_session)) -> None:
    service = TaskService(session)
    await service.delete_task(task_id)
