from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SavedViewCreate(BaseModel):
    name: str
    settings: dict[str, Any]


class SavedViewUpdate(BaseModel):
    name: str | None = None
    settings: dict[str, Any] | None = None


class SavedViewResponse(BaseModel):
    id: int
    name: str
    settings: dict[str, Any]
    owner_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
