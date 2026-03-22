from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_token
from app.models.api_token import APIToken
from app.schemas.api_token import APITokenCreate


class APITokenService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, owner_id: int, data: APITokenCreate) -> tuple[APIToken, str]:
        """Create a token. Returns (ORM object, raw_token). Raw token shown once."""
        raw, token_hash, prefix = generate_api_token()

        token = APIToken(
            name=data.name,
            token_hash=token_hash,
            prefix=prefix,
            owner_id=owner_id,
            expires_at=data.expires_at,
        )
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token, raw

    async def list_tokens(self, owner_id: int) -> list[APIToken]:
        result = await self.db.execute(
            select(APIToken).where(APIToken.owner_id == owner_id).order_by(APIToken.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke(self, token_id: int, owner_id: int) -> APIToken:
        token = await self._get(token_id, owner_id)
        token.is_active = False
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def delete(self, token_id: int, owner_id: int) -> None:
        token = await self._get(token_id, owner_id)
        await self.db.delete(token)
        await self.db.commit()

    async def _get(self, token_id: int, owner_id: int) -> APIToken:
        result = await self.db.execute(
            select(APIToken).where(APIToken.id == token_id, APIToken.owner_id == owner_id)
        )
        token = result.scalar_one_or_none()
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        return token
