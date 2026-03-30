from datetime import datetime, timedelta, timezone


def test_tasks_crud(client):
    now = datetime.now(timezone.utc) + timedelta(days=1)

    create_res = client.post(
        "/api/tasks",
        json={
            "title": "Write docs",
            "description": "prepare README",
            "status": "pending",
            "priority": "high",
            "due_date": now.isoformat(),
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    task_id = created["id"]
    assert created["title"] == "Write docs"

    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    detail_res = client.get(f"/api/tasks/{task_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["priority"] == "high"

    patch_res = client.patch(
        f"/api/tasks/{task_id}",
        json={"status": "completed", "priority": "medium"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

    delete_res = client.delete(f"/api/tasks/{task_id}")
    assert delete_res.status_code == 204


def test_tasks_filters(client):
    now = datetime.now(timezone.utc)
    payloads = [
        {
            "title": "Task A",
            "status": "pending",
            "priority": "low",
            "due_date": (now + timedelta(days=1)).isoformat(),
        },
        {
            "title": "Task B",
            "status": "in_progress",
            "priority": "high",
            "due_date": (now + timedelta(days=2)).isoformat(),
        },
    ]

    for payload in payloads:
        res = client.post("/api/tasks", json=payload)
        assert res.status_code == 201

    res = client.get("/api/tasks", params={"status": "in_progress"})
    assert res.status_code == 200
    assert all(item["status"] == "in_progress" for item in res.json()["items"])

    res = client.get("/api/tasks", params={"priority": "low"})
    assert res.status_code == 200
    assert all(item["priority"] == "low" for item in res.json()["items"])


def test_complete_task_endpoint(client):
    now = datetime.now(timezone.utc) + timedelta(days=1)
    create_res = client.post(
        "/api/tasks",
        json={
            "title": "Task to complete",
            "status": "pending",
            "priority": "medium",
            "due_date": now.isoformat(),
        },
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    complete_res = client.patch(f"/api/tasks/{task_id}/complete")
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"
    assert complete_res.json()["completed_at"] is not None
