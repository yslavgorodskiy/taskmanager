from datetime import datetime

from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str = "#10b981"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
