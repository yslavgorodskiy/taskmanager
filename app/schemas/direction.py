from datetime import datetime

from pydantic import BaseModel, field_validator


class DirectionCreate(BaseModel):
    name: str
    description: str | None = None
    color: str = "#6366f1"

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be a 7-character hex code, e.g. #6366f1")
        return v


class DirectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class DirectionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    color: str
    owner_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
