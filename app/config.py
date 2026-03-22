from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TaskManager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/taskmanager"

    # JWT
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API tokens
    API_TOKEN_PREFIX: str = "tm_"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
