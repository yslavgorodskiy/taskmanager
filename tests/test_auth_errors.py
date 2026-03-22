"""Edge-case tests for auth and dependency error paths."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_no_credentials(client: AsyncClient):
    """Request without any auth token returns 401."""
    resp = await client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_jwt(client: AsyncClient):
    """Malformed JWT returns 401."""
    resp = await client.get("/users/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token(client: AsyncClient):
    """Using an access token where a refresh token is expected returns 401."""
    await client.post("/auth/register", json={"email": "r@example.com", "password": "pass1234"})
    login = await client.post("/auth/login", json={"email": "r@example.com", "password": "pass1234"})
    access_token = login.json()["access_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    """Garbage refresh token returns 401."""
    resp = await client.post("/auth/refresh", json={"refresh_token": "garbage"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key(client: AsyncClient):
    """Unknown X-API-Token returns 401."""
    resp = await client.get("/users/me", headers={"X-API-Token": "tm_nonexistent"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_returns_400(client: AsyncClient):
    """Duplicate registration via AuthService raises 400."""
    payload = {"email": "dup@example.com", "password": "pass1234"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]
