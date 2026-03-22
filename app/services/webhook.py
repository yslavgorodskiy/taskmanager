import json
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import sign_webhook_payload
from app.database import AsyncSessionLocal
from app.models.webhook import Webhook, WebhookDelivery

# All event types emitted by this application
WEBHOOK_EVENTS: frozenset[str] = frozenset(
    {
        "task.created",
        "task.updated",
        "task.status_changed",
        "task.deleted",
    }
)


class WebhookService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(
        self,
        owner_id: int,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Find active webhooks subscribed to *event_type* and deliver the event."""
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.owner_id == owner_id,
                Webhook.is_active.is_(True),
            )
        )
        webhooks = result.scalars().all()

        for webhook in webhooks:
            if event_type in webhook.events or "*" in webhook.events:
                await self._deliver(webhook, event_type, payload)

    async def _deliver(
        self,
        webhook: Webhook,
        event_type: str,
        payload: dict[str, Any],
    ) -> WebhookDelivery:
        body = json.dumps(
            {
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": payload,
            },
            default=str,
        )
        signature = sign_webhook_payload(body, webhook.secret)

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Event": event_type,
                        "X-Webhook-Signature": signature,
                    },
                )
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:2000]
            delivery.success = 200 <= response.status_code < 300
        except Exception as exc:
            delivery.response_body = str(exc)[:2000]
            delivery.success = False

        self.db.add(delivery)
        await self.db.commit()
        return delivery


async def dispatch_webhook_event(
    owner_id: int, event_type: str, payload: dict[str, Any]
) -> None:
    """Standalone coroutine for FastAPI BackgroundTasks — opens its own DB session."""
    async with AsyncSessionLocal() as db:
        await WebhookService(db).dispatch(owner_id, event_type, payload)
