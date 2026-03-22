import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/tasks/",
        json={"title": "Buy groceries", "priority": "high"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Buy groceries"
    assert data["status"] == "new"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_headers: dict):
    for i in range(3):
        await client.post("/tasks/", json={"title": f"Task {i}"}, headers=auth_headers)
    resp = await client.get("/tasks/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client: AsyncClient, auth_headers: dict):
    await client.post("/tasks/", json={"title": "New task", "status": "new"}, headers=auth_headers)
    await client.post("/tasks/", json={"title": "Done task", "status": "completed"}, headers=auth_headers)

    resp = await client.get("/tasks/?status=new", headers=auth_headers)
    assert resp.status_code == 200
    assert all(t["status"] == "new" for t in resp.json())


@pytest.mark.asyncio
async def test_update_task_status(client: AsyncClient, auth_headers: dict):
    create = await client.post("/tasks/", json={"title": "T"}, headers=auth_headers)
    task_id = create.json()["id"]

    resp = await client.patch(f"/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers: dict):
    create = await client.post("/tasks/", json={"title": "To delete"}, headers=auth_headers)
    task_id = create.json()["id"]

    resp = await client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_task_with_direction_and_tags(client: AsyncClient, auth_headers: dict):
    dir_resp = await client.post(
        "/directions/", json={"name": "Work", "color": "#123456"}, headers=auth_headers
    )
    direction_id = dir_resp.json()["id"]

    tag_resp = await client.post("/tags/", json={"name": "urgent"}, headers=auth_headers)
    tag_id = tag_resp.json()["id"]

    resp = await client.post(
        "/tasks/",
        json={"title": "Work task", "direction_id": direction_id, "tag_ids": [tag_id]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["direction"]["id"] == direction_id
    assert any(t["id"] == tag_id for t in data["tags"])
