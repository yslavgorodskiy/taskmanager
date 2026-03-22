from datetime import datetime

from pydantic import BaseModel

from app.models.task import TaskPriority, TaskStatus
from app.schemas.direction import DirectionResponse
from app.schemas.tag import TagResponse


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    direction_id: int | None = None
    tag_ids: list[int] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    direction_id: int | None = None
    tag_ids: list[int] | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    owner_id: int
    direction_id: int | None
    direction: DirectionResponse | None
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
