from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class APIToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # SHA-256 hash of the raw token — never store the plaintext
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    # First 12 chars displayed to users so they can identify tokens without the secret
    prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = mapped_column(DateTime(timezone=True))

    owner = relationship("User", back_populates="api_tokens")
