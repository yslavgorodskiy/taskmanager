from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.saved_view import SavedView
from app.models.user import User
from app.schemas.saved_view import SavedViewCreate, SavedViewResponse, SavedViewUpdate

router = APIRouter(prefix="/saved-views", tags=["Saved Views"])


@router.get("/", response_model=list[SavedViewResponse], summary="List saved views")
async def list_saved_views(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedViewResponse]:
    result = await db.execute(
        select(SavedView)
        .where(SavedView.owner_id == current_user.id)
        .order_by(SavedView.created_at)
    )
    return result.scalars().all()


@router.post("/", response_model=SavedViewResponse, status_code=201, summary="Create saved view")
async def create_saved_view(
    data: SavedViewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SavedViewResponse:
    view = SavedView(
        name=data.name,
        settings=data.settings,
        owner_id=current_user.id,
    )
    db.add(view)
    await db.flush()
    await db.refresh(view)
    return view


@router.patch("/{view_id}", response_model=SavedViewResponse, summary="Update a saved view")
async def update_saved_view(
    view_id: int,
    data: SavedViewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SavedViewResponse:
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.owner_id == current_user.id,
        )
    )
    view = result.scalar_one_or_none()
    if view is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found")
    if data.name is not None:
        view.name = data.name
    if data.settings is not None:
        view.settings = data.settings
    await db.flush()
    await db.refresh(view)
    return view


@router.delete("/{view_id}", status_code=204, summary="Delete a saved view")
async def delete_saved_view(
    view_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.owner_id == current_user.id,
        )
    )
    view = result.scalar_one_or_none()
    if view is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found")
    await db.delete(view)
