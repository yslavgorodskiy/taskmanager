import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_direction(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/directions/", json={"name": "Work", "color": "#ff0000"}, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Work"
    assert data["color"] == "#ff0000"


@pytest.mark.asyncio
async def test_list_directions(client: AsyncClient, auth_headers: dict):
    await client.post("/directions/", json={"name": "Work"}, headers=auth_headers)
    await client.post("/directions/", json={"name": "Personal"}, headers=auth_headers)
    resp = await client.get("/directions/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_direction(client: AsyncClient, auth_headers: dict):
    create = await client.post("/directions/", json={"name": "Work"}, headers=auth_headers)
    direction_id = create.json()["id"]

    resp = await client.get(f"/directions/{direction_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Work"


@pytest.mark.asyncio
async def test_get_direction_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/directions/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_direction(client: AsyncClient, auth_headers: dict):
    create = await client.post("/directions/", json={"name": "Old"}, headers=auth_headers)
    direction_id = create.json()["id"]

    resp = await client.patch(
        f"/directions/{direction_id}", json={"name": "New"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_direction(client: AsyncClient, auth_headers: dict):
    create = await client.post("/directions/", json={"name": "To delete"}, headers=auth_headers)
    direction_id = create.json()["id"]

    resp = await client.delete(f"/directions/{direction_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/directions/{direction_id}", headers=auth_headers)
    assert resp.status_code == 404
