from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import TaskPriority, TaskStatus
from core.exceptions import NotFoundException, ValidationException
from core.utils import utcnow
from modules.tasks.models import Task
from modules.tasks.repository import TaskRepository
from modules.tasks.schemas import TaskCreate, TaskStatsResponse, TaskUpdate


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TaskRepository(session)

    async def create_task(self, payload: TaskCreate) -> Task:
        if payload.due_date and payload.due_date < utcnow():
            raise ValidationException("Due date cannot be in the past")

        task = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            due_date=payload.due_date,
            completed_at=utcnow() if payload.status == TaskStatus.COMPLETED else None,
        )
        created = await self.repo.create(task)
        await self.session.commit()
        return created

    async def get_task(self, task_id: int) -> Task:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundException("Task not found")
        return task

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date_from: datetime | None = None,
        due_date_to: datetime | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        if due_date_from and due_date_to and due_date_from > due_date_to:
            raise ValidationException("due_date_from cannot be greater than due_date_to")
        return await self.repo.list(status, priority, due_date_from, due_date_to, search)

    async def update_task(self, task_id: int, payload: TaskUpdate) -> Task:
        task = await self.get_task(task_id)

        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description
        if payload.priority is not None:
            task.priority = payload.priority
        if payload.due_date is not None:
            task.due_date = payload.due_date
        if payload.status is not None:
            old_status = task.status
            task.status = payload.status
            if old_status != TaskStatus.COMPLETED and payload.status == TaskStatus.COMPLETED:
                task.completed_at = utcnow()
            if old_status == TaskStatus.COMPLETED and payload.status != TaskStatus.COMPLETED:
                task.completed_at = None

        updated = await self.repo.update(task)
        await self.session.commit()
        return updated

    async def delete_task(self, task_id: int) -> None:
        task = await self.get_task(task_id)
        await self.repo.delete(task)
        await self.session.commit()

    async def complete_task(self, task_id: int) -> Task:
        task = await self.get_task(task_id)
        if task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = utcnow()
            updated = await self.repo.update(task)
            await self.session.commit()
            return updated
        return task

    async def task_stats(self) -> TaskStatsResponse:
        by_status = await self.repo.count_by_status()
        by_priority = await self.repo.count_by_priority()
        _, total = await self.repo.list()
        return TaskStatsResponse(total=total, by_status=by_status, by_priority=by_priority)

    async def count_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date_from: datetime | None = None,
        due_date_to: datetime | None = None,
    ) -> int:
        _, total = await self.repo.list(status, priority, due_date_from, due_date_to)
        return total

    async def complete_tasks_by_filter(
        self, status: TaskStatus | None = None, priority: TaskPriority | None = None
    ) -> dict[str, int]:
        tasks, _ = await self.repo.list(status=status, priority=priority)
        changed = 0
        for task in tasks:
            if task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.COMPLETED
                task.completed_at = utcnow()
                changed += 1

        await self.session.commit()
        return {"updated": changed}

    async def delete_completed_tasks(self) -> dict[str, int]:
        deleted = await self.repo.delete_completed()
        await self.session.commit()
        return {"deleted": deleted}

    async def get_urgent_task(self) -> Task | None:
        tasks, _ = await self.repo.list(status=TaskStatus.PENDING)
        if not tasks:
            return None
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                0 if t.priority == TaskPriority.HIGH else 1,
                t.due_date or datetime.max,
            ),
        )
        return sorted_tasks[0]
