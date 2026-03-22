import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_full_name(client: AsyncClient, auth_headers: dict):
    resp = await client.patch(
        "/users/me", json={"full_name": "Alice Smith"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alice Smith"


@pytest.mark.asyncio
async def test_update_password(client: AsyncClient, auth_headers: dict):
    resp = await client.patch(
        "/users/me", json={"password": "newpassword123"}, headers=auth_headers
    )
    assert resp.status_code == 200

    # Old password should no longer work
    login = await client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )
    assert login.status_code == 401

    # New password should work
    login = await client.post(
        "/auth/login", json={"email": "user@example.com", "password": "newpassword123"}
    )
    assert login.status_code == 200
