from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.direction import Direction
from app.models.user import User
from app.schemas.direction import DirectionCreate, DirectionResponse, DirectionUpdate

router = APIRouter(prefix="/directions", tags=["Directions"])


@router.post("/", response_model=DirectionResponse, status_code=201, summary="Create a direction")
async def create_direction(
    data: DirectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DirectionResponse:
    direction = Direction(**data.model_dump(), owner_id=current_user.id)
    db.add(direction)
    await db.commit()
    await db.refresh(direction)
    return direction


@router.get("/", response_model=list[DirectionResponse], summary="List all directions")
async def list_directions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[DirectionResponse]:
    result = await db.execute(
        select(Direction)
        .where(Direction.owner_id == current_user.id)
        .order_by(Direction.name)
    )
    return list(result.scalars().all())


@router.get("/{direction_id}", response_model=DirectionResponse, summary="Get a direction")
async def get_direction(
    direction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DirectionResponse:
    return await _get_or_404(direction_id, current_user.id, db)


@router.patch("/{direction_id}", response_model=DirectionResponse, summary="Update a direction")
async def update_direction(
    direction_id: int,
    data: DirectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DirectionResponse:
    direction = await _get_or_404(direction_id, current_user.id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(direction, field, value)
    await db.commit()
    await db.refresh(direction)
    return direction


@router.delete("/{direction_id}", status_code=204, summary="Delete a direction")
async def delete_direction(
    direction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    direction = await _get_or_404(direction_id, current_user.id, db)
    await db.delete(direction)
    await db.commit()


async def _get_or_404(direction_id: int, owner_id: int, db: AsyncSession) -> Direction:
    result = await db.execute(
        select(Direction).where(Direction.id == direction_id, Direction.owner_id == owner_id)
    )
    direction = result.scalar_one_or_none()
    if direction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Direction not found")
    return direction
