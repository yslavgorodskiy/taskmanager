import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/tags/", json={"name": "urgent", "color": "#ff0000"}, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "urgent"


@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient, auth_headers: dict):
    await client.post("/tags/", json={"name": "work"}, headers=auth_headers)
    await client.post("/tags/", json={"name": "personal"}, headers=auth_headers)
    resp = await client.get("/tags/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_tag(client: AsyncClient, auth_headers: dict):
    create = await client.post("/tags/", json={"name": "work"}, headers=auth_headers)
    tag_id = create.json()["id"]

    resp = await client.get(f"/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "work"


@pytest.mark.asyncio
async def test_get_tag_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/tags/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient, auth_headers: dict):
    create = await client.post("/tags/", json={"name": "old"}, headers=auth_headers)
    tag_id = create.json()["id"]

    resp = await client.patch(f"/tags/{tag_id}", json={"name": "new"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "new"


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient, auth_headers: dict):
    create = await client.post("/tags/", json={"name": "to-delete"}, headers=auth_headers)
    tag_id = create.json()["id"]

    resp = await client.delete(f"/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 404
