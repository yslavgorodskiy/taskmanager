from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.direction import Direction
from app.models.tag import Tag, task_tags
from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.webhook import dispatch_webhook_event


class TaskService:
    def __init__(self, db: AsyncSession, background_tasks: BackgroundTasks) -> None:
        self.db = db
        self.bg = background_tasks

    # ------------------------------------------------------------------ helpers

    async def _fetch(self, task_id: int, owner_id: int) -> Task:
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.tags), selectinload(Task.direction))
            .where(Task.id == task_id, Task.owner_id == owner_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    async def _resolve_tags(self, tag_ids: list[int], owner_id: int) -> list[Tag]:
        if not tag_ids:
            return []
        result = await self.db.execute(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.owner_id == owner_id)
        )
        tags = list(result.scalars().all())
        if len(tags) != len(tag_ids):
            raise HTTPException(status_code=404, detail="One or more tags not found")
        return tags

    async def _resolve_direction(self, direction_id: int, owner_id: int) -> None:
        result = await self.db.execute(
            select(Direction).where(
                Direction.id == direction_id, Direction.owner_id == owner_id
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Direction not found")

    def _fire(self, event: str, owner_id: int, payload: dict) -> None:
        self.bg.add_task(dispatch_webhook_event, owner_id, event, payload)

    # ------------------------------------------------------------------ CRUD

    async def create(self, owner_id: int, data: TaskCreate) -> Task:
        if data.direction_id:
            await self._resolve_direction(data.direction_id, owner_id)

        tags = await self._resolve_tags(data.tag_ids, owner_id)

        task = Task(
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            owner_id=owner_id,
            direction_id=data.direction_id,
            tags=tags,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        task = await self._fetch(task.id, owner_id)
        self._fire("task.created", owner_id, {"task_id": task.id, "title": task.title})
        return task

    async def get_list(
        self,
        owner_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        direction_id: int | None = None,
        tag_ids: list[int] | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Task]:
        query = (
            select(Task)
            .options(selectinload(Task.tags), selectinload(Task.direction))
            .where(Task.owner_id == owner_id)
        )
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if direction_id:
            query = query.where(Task.direction_id == direction_id)
        if tag_ids:
            # Keep only tasks that have at least one of the requested tags
            subq = select(task_tags.c.task_id).where(task_tags.c.tag_id.in_(tag_ids))
            query = query.where(Task.id.in_(subq))

        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, task_id: int, owner_id: int) -> Task:
        return await self._fetch(task_id, owner_id)

    async def update(self, task_id: int, owner_id: int, data: TaskUpdate) -> Task:
        task = await self._fetch(task_id, owner_id)
        old_status = task.status

        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status
        if data.priority is not None:
            task.priority = data.priority
        if data.due_date is not None:
            task.due_date = data.due_date
        if data.direction_id is not None:
            await self._resolve_direction(data.direction_id, owner_id)
            task.direction_id = data.direction_id
        if data.tag_ids is not None:
            task.tags = await self._resolve_tags(data.tag_ids, owner_id)

        await self.db.commit()
        task = await self._fetch(task_id, owner_id)

        self._fire("task.updated", owner_id, {"task_id": task.id, "title": task.title})
        if data.status and old_status != data.status:
            self._fire(
                "task.status_changed",
                owner_id,
                {"task_id": task.id, "old_status": old_status, "new_status": task.status},
            )
        return task

    async def delete(self, task_id: int, owner_id: int) -> None:
        task = await self._fetch(task_id, owner_id)
        self._fire("task.deleted", owner_id, {"task_id": task_id})
        await self.db.delete(task)
        await self.db.commit()
