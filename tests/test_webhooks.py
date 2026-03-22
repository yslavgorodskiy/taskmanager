import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient):
    resp = await client.get("/webhooks/events")
    assert resp.status_code == 200
    assert "task.created" in resp.json()


@pytest.mark.asyncio
async def test_create_webhook(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/webhooks/",
        json={"name": "My hook", "url": "https://example.com/hook", "events": ["task.created"]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My hook"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_webhooks(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/webhooks/",
        json={"name": "Hook 1", "url": "https://example.com/1", "events": ["*"]},
        headers=auth_headers,
    )
    resp = await client.get("/webhooks/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_webhook(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/webhooks/",
        json={"name": "Hook", "url": "https://example.com/hook", "events": ["*"]},
        headers=auth_headers,
    )
    webhook_id = create.json()["id"]

    resp = await client.get(f"/webhooks/{webhook_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == webhook_id


@pytest.mark.asyncio
async def test_get_webhook_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/webhooks/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_webhook(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/webhooks/",
        json={"name": "Old", "url": "https://example.com/hook", "events": ["*"]},
        headers=auth_headers,
    )
    webhook_id = create.json()["id"]

    resp = await client.patch(
        f"/webhooks/{webhook_id}", json={"name": "New", "is_active": False}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_webhook(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/webhooks/",
        json={"name": "To delete", "url": "https://example.com/hook", "events": ["*"]},
        headers=auth_headers,
    )
    webhook_id = create.json()["id"]

    resp = await client.delete(f"/webhooks/{webhook_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/webhooks/{webhook_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_deliveries(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/webhooks/",
        json={"name": "Hook", "url": "https://example.com/hook", "events": ["*"]},
        headers=auth_headers,
    )
    webhook_id = create.json()["id"]

    resp = await client.get(f"/webhooks/{webhook_id}/deliveries", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
