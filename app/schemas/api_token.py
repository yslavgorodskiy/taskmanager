from datetime import datetime

from pydantic import BaseModel


class APITokenCreate(BaseModel):
    name: str
    expires_at: datetime | None = None


class APITokenResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class APITokenCreatedResponse(APITokenResponse):
    """Returned only on creation — token is shown once and never stored in plaintext."""

    token: str
