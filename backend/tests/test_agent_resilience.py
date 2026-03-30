"""Tests for agent chat endpoint resilience — must handle AI unavailability gracefully."""

from datetime import datetime, timedelta, timezone


def test_agent_chat_with_ai_disabled(client):
    """When AI is disabled, chat should return a controlled fallback response (not 500)."""
    response = client.post("/api/agent/chat", json={
        "message": "muéstrame las tareas pendientes",
        "session_id": "test-session",
    })
    assert response.status_code == 200
    body = response.json()

    assert body["success"] is False
    assert body["provider_available"] is False
    assert body["fallback_mode"] is True
    assert "answer" in body
    assert len(body["answer"]) > 0
    assert "history" in body


def test_agent_chat_returns_history(client):
    """Even with AI disabled, the chat should accumulate history."""
    session_id = "test-history"

    # first message
    r1 = client.post("/api/agent/chat", json={
        "message": "hola",
        "session_id": session_id,
    })
    assert r1.status_code == 200
    assert len(r1.json()["history"]) == 2  # user + assistant

    # second message
    r2 = client.post("/api/agent/chat", json={
        "message": "otra pregunta",
        "session_id": session_id,
    })
    assert r2.status_code == 200
    assert len(r2.json()["history"]) == 4  # 2 previous + 2 new


def test_agent_clear_history_with_ai_disabled(client):
    """Clear history must work even with AI disabled."""
    # Send a message first
    client.post("/api/agent/chat", json={
        "message": "test message",
        "session_id": "clear-test",
    })

    # Clear
    response = client.delete("/api/agent/history?session_id=clear-test")
    assert response.status_code == 204


def test_crud_works_with_ai_disabled(client):
    """Core CRUD must work perfectly when AI is disabled."""
    now = datetime.now(timezone.utc) + timedelta(days=1)

    # CREATE
    create_res = client.post("/api/tasks", json={
        "title": "Task without AI",
        "description": "This must work without AI",
        "status": "pending",
        "priority": "high",
        "due_date": now.isoformat(),
    })
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]
    assert create_res.json()["title"] == "Task without AI"

    # READ
    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Task without AI"

    # LIST
    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # UPDATE
    patch_res = client.patch(f"/api/tasks/{task_id}", json={
        "status": "completed",
        "priority": "medium",
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

    # DELETE
    del_res = client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 204


def test_task_filters_with_ai_disabled(client):
    """Filters must work without AI."""
    now = datetime.now(timezone.utc)

    client.post("/api/tasks", json={
        "title": "Filter task A",
        "status": "pending",
        "priority": "low",
        "due_date": (now + timedelta(days=1)).isoformat(),
    })
    client.post("/api/tasks", json={
        "title": "Filter task B",
        "status": "in_progress",
        "priority": "high",
        "due_date": (now + timedelta(days=2)).isoformat(),
    })

    # Filter by status
    res = client.get("/api/tasks", params={"status": "pending"})
    assert res.status_code == 200
    assert all(item["status"] == "pending" for item in res.json()["items"])

    # Filter by priority
    res = client.get("/api/tasks", params={"priority": "high"})
    assert res.status_code == 200
    assert all(item["priority"] == "high" for item in res.json()["items"])


def test_ai_status_endpoint(client):
    """The AI status endpoint must be accessible and report current state."""
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert "ai_enabled" in body
    assert "provider" in body
    assert "available" in body
    assert "model" in body
    assert "allow_fallback" in body


def test_ai_health_endpoint(client):
    response = client.get("/api/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert "provider" in body["data"]
    assert "can_chat" in body["data"]


def test_ai_chat_wrapper_endpoint(client):
    response = client.post(
        "/api/ai/chat",
        json={
            "message": "crea una tarea de prueba",
            "session_id": "wrapper-session",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "success" in body["data"]
    assert "provider_available" in body["data"]
