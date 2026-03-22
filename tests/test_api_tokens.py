import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_api_token(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api-tokens/", json={"name": "My token"}, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My token"
    assert data["token"].startswith("tm_")


@pytest.mark.asyncio
async def test_list_api_tokens(client: AsyncClient, auth_headers: dict):
    await client.post("/api-tokens/", json={"name": "Token 1"}, headers=auth_headers)
    await client.post("/api-tokens/", json={"name": "Token 2"}, headers=auth_headers)
    resp = await client.get("/api-tokens/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_revoke_api_token(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api-tokens/", json={"name": "To revoke"}, headers=auth_headers)
    token_id = create.json()["id"]

    resp = await client.post(f"/api-tokens/{token_id}/revoke", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_api_token(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api-tokens/", json={"name": "To delete"}, headers=auth_headers)
    token_id = create.json()["id"]

    resp = await client.delete(f"/api-tokens/{token_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_auth_with_api_token(client: AsyncClient, auth_headers: dict):
    """X-API-Token header should work as an alternative to Bearer JWT."""
    create = await client.post("/api-tokens/", json={"name": "CI token"}, headers=auth_headers)
    raw_token = create.json()["token"]

    resp = await client.get("/users/me", headers={"X-API-Token": raw_token})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"
