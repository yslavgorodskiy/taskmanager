from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.security import generate_webhook_secret
from app.database import get_db
from app.models.user import User
from app.models.webhook import Webhook, WebhookDelivery
from app.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookUpdate,
)
from app.services.webhook import WEBHOOK_EVENTS, dispatch_webhook_event

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/events", response_model=list[str], summary="List supported event types")
async def list_events() -> list[str]:
    return sorted(WEBHOOK_EVENTS)


@router.post("/", response_model=WebhookResponse, status_code=201, summary="Create a webhook")
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    webhook = Webhook(
        name=data.name,
        url=data.url,
        secret=generate_webhook_secret(),
        events=data.events,
        owner_id=current_user.id,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.get("/", response_model=list[WebhookResponse], summary="List webhooks")
async def list_webhooks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookResponse]:
    result = await db.execute(
        select(Webhook).where(Webhook.owner_id == current_user.id).order_by(Webhook.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{webhook_id}", response_model=WebhookResponse, summary="Get a webhook")
async def get_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    return await _get_or_404(webhook_id, current_user.id, db)


@router.patch("/{webhook_id}", response_model=WebhookResponse, summary="Update a webhook")
async def update_webhook(
    webhook_id: int,
    data: WebhookUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    webhook = await _get_or_404(webhook_id, current_user.id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(webhook, field, value)
    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", status_code=204, summary="Delete a webhook")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    webhook = await _get_or_404(webhook_id, current_user.id, db)
    await db.delete(webhook)
    await db.commit()


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryResponse],
    summary="List recent delivery attempts",
)
async def list_deliveries(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookDeliveryResponse]:
    await _get_or_404(webhook_id, current_user.id, db)
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.post(
    "/{webhook_id}/test",
    status_code=202,
    summary="Send a test event to verify the endpoint",
)
async def test_webhook(
    webhook_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _get_or_404(webhook_id, current_user.id, db)
    background_tasks.add_task(
        dispatch_webhook_event,
        current_user.id,
        "task.created",
        {"test": True, "webhook_id": webhook_id},
    )
    return {"message": "Test event queued"}


async def _get_or_404(webhook_id: int, owner_id: int, db: AsyncSession) -> Webhook:
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.owner_id == owner_id)
    )
    webhook = result.scalar_one_or_none()
    if webhook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return webhook
