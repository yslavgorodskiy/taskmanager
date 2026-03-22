from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.api_token import APITokenCreate, APITokenCreatedResponse, APITokenResponse
from app.services.api_token import APITokenService

router = APIRouter(prefix="/api-tokens", tags=["API Tokens"])


@router.post(
    "/",
    response_model=APITokenCreatedResponse,
    status_code=201,
    summary="Create an API token (raw token shown only once)",
)
async def create_api_token(
    data: APITokenCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APITokenCreatedResponse:
    token_obj, raw_token = await APITokenService(db).create(current_user.id, data)
    response = APITokenCreatedResponse.model_validate(token_obj)
    response.token = raw_token
    return response


@router.get("/", response_model=list[APITokenResponse], summary="List API tokens")
async def list_api_tokens(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[APITokenResponse]:
    return await APITokenService(db).list_tokens(current_user.id)


@router.post("/{token_id}/revoke", response_model=APITokenResponse, summary="Revoke an API token")
async def revoke_api_token(
    token_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APITokenResponse:
    return await APITokenService(db).revoke(token_id, current_user.id)


@router.delete("/{token_id}", status_code=204, summary="Permanently delete an API token")
async def delete_api_token(
    token_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await APITokenService(db).delete(token_id, current_user.id)
