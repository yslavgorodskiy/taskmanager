from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, hash_api_token
from app.database import get_db
from app.models.api_token import APIToken
from app.models.user import User

# OAuth2 scheme — points at the login endpoint for Swagger UI's Authorize button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)

_unauthorized = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    jwt_token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the caller from either a JWT Bearer token or an X-API-Token header."""
    if jwt_token:
        return await _user_from_jwt(jwt_token, db)
    if api_key:
        return await _user_from_api_key(api_key, db)
    raise _unauthorized


async def _user_from_jwt(token: str, db: AsyncSession) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise _unauthorized
        user_id = payload.get("sub")
        if user_id is None:
            raise _unauthorized
    except JWTError:
        raise _unauthorized

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _unauthorized
    return user


async def _user_from_api_key(api_key: str, db: AsyncSession) -> User:
    token_hash = hash_api_token(api_key)
    result = await db.execute(
        select(APIToken).where(
            APIToken.token_hash == token_hash,
            APIToken.is_active.is_(True),
        )
    )
    api_token = result.scalar_one_or_none()
    if api_token is None:
        raise _unauthorized

    if api_token.expires_at and api_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token has expired",
        )

    # Track last usage (best-effort, ignore commit failure)
    api_token.last_used_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except Exception:
        await db.rollback()

    result = await db.execute(select(User).where(User.id == api_token.owner_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _unauthorized
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
