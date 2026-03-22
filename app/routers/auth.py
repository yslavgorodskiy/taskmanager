from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user account",
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse, summary="Obtain JWT tokens")
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    access, refresh = await AuthService(db).authenticate(credentials.email, credentials.password)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    access, refresh = await AuthService(db).refresh_tokens(data.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)
