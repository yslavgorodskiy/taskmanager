"""
Shared pytest fixtures.

Uses an in-memory SQLite database so tests have no external dependencies.
- StaticPool ensures all sessions share the same in-memory DB connection.
- asyncio_default_fixture_loop_scope = session (pytest.ini) keeps a single
  event loop for the whole test run so the module-level engine stays valid.
- dispatch_webhook_event is mocked so no real DB/network calls happen in bg tasks.
"""

from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="session")
async def create_tables():
    """Create all tables once for the entire test session."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate all data between tests to ensure isolation."""
    yield
    async with _TestSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def db_session():
    async with _TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock webhook background tasks — prevents real DB sessions or HTTP calls
    with patch("app.services.task.dispatch_webhook_event", new=AsyncMock()):
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
