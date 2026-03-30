from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import TaskPriority, TaskStatus
from modules.tasks.models import Task


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: int) -> Task | None:
        query = select(Task).where(Task.id == task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date_from: datetime | None = None,
        due_date_to: datetime | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        filters = []
        if status:
            filters.append(Task.status == status)
        if priority:
            filters.append(Task.priority == priority)
        if due_date_from:
            filters.append(Task.due_date >= due_date_from)
        if due_date_to:
            filters.append(Task.due_date <= due_date_to)
        if search:
            like = f"%{search.strip()}%"
            filters.append(Task.title.ilike(like) | Task.description.ilike(like))

        where_clause = and_(*filters) if filters else None
        query = select(Task).order_by(Task.due_date.asc().nulls_last(), Task.id.desc())
        count_query = select(func.count(Task.id))

        if where_clause is not None:
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)

        items_result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)
        items = list(items_result.scalars().all())
        total = int(count_result.scalar_one())
        return items, total

    async def update(self, task: Task) -> Task:
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)

    async def delete_completed(self) -> int:
        stmt = delete(Task).where(Task.status == TaskStatus.COMPLETED)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def count_by_status(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        )
        rows = result.all()
        return {row[0].value: row[1] for row in rows}

    async def count_by_priority(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        )
        rows = result.all()
        return {row[0].value: row[1] for row in rows}
