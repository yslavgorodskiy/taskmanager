from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.post("/", response_model=TagResponse, status_code=201, summary="Create a tag")
async def create_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    tag = Tag(**data.model_dump(), owner_id=current_user.id)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("/", response_model=list[TagResponse], summary="List all tags")
async def list_tags(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[TagResponse]:
    result = await db.execute(
        select(Tag).where(Tag.owner_id == current_user.id).order_by(Tag.name)
    )
    return list(result.scalars().all())


@router.get("/{tag_id}", response_model=TagResponse, summary="Get a tag")
async def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    return await _get_or_404(tag_id, current_user.id, db)


@router.patch("/{tag_id}", response_model=TagResponse, summary="Update a tag")
async def update_tag(
    tag_id: int,
    data: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    tag = await _get_or_404(tag_id, current_user.id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204, summary="Delete a tag")
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    tag = await _get_or_404(tag_id, current_user.id, db)
    await db.delete(tag)
    await db.commit()


async def _get_or_404(tag_id: int, owner_id: int, db: AsyncSession) -> Tag:
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.owner_id == owner_id)
    )
    tag = result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag
