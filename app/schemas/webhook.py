from datetime import datetime

from pydantic import BaseModel, field_validator


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: list[str]

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one event type must be specified")
        return v


class WebhookUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: list[str]
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: int
    webhook_id: int
    event_type: str
    payload: dict
    response_status: int | None
    response_body: str | None
    attempt_count: int
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}
