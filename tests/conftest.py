"""
Shared pytest fixtures.

Uses an in-memory SQLite database so tests have no external dependencies.
AsyncSessionLocal is patched globally so background tasks (webhook dispatch)
also use the test DB instead of the real PostgreSQL connection.
"""

from unittest.mock import patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database as app_database
import app.services.webhook as webhook_service_module
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with _TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Patch AsyncSessionLocal used by background webhook dispatch so it
    # doesn't open a real PostgreSQL connection during tests.
    with patch.object(app_database, "AsyncSessionLocal", _TestSessionLocal), \
         patch.object(webhook_service_module, "AsyncSessionLocal", _TestSessionLocal):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_and_login(client: AsyncClient, email: str = "user@example.com") -> dict:
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    resp = await client.post("/auth/login", json={"email": email, "password": "password123"})
    return resp.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    tokens = await _register_and_login(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
