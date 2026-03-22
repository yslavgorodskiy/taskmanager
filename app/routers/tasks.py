from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=201, summary="Create a task")
async def create_task(
    data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await TaskService(db, background_tasks).create(current_user.id, data)


@router.get(
    "/",
    response_model=list[TaskResponse],
    summary="List tasks with optional filters",
)
async def list_tasks(
    background_tasks: BackgroundTasks,
    status: TaskStatus | None = Query(None),
    priority: TaskPriority | None = Query(None),
    direction_id: int | None = Query(None),
    tag_ids: list[int] | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    return await TaskService(db, background_tasks).get_list(
        current_user.id, status, priority, direction_id, tag_ids, skip, limit
    )


@router.get("/{task_id}", response_model=TaskResponse, summary="Get a task by ID")
async def get_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await TaskService(db, background_tasks).get(task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskResponse, summary="Update a task")
async def update_task(
    task_id: int,
    data: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await TaskService(db, background_tasks).update(task_id, current_user.id, data)


@router.delete("/{task_id}", status_code=204, summary="Delete a task")
async def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await TaskService(db, background_tasks).delete(task_id, current_user.id)
