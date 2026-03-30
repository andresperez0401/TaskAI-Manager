"""Tests for summary endpoint resilience — must work with AI disabled."""

from datetime import datetime, timedelta, timezone


def test_summary_today_returns_stats_with_ai_disabled(client):
    """Summary endpoint must return structured stats even with AI_ENABLED=false."""
    response = client.get("/api/summary/today")
    assert response.status_code == 200
    body = response.json()

    # New contract: stats object
    assert "stats" in body
    stats = body["stats"]
    assert "total_tasks" in stats
    assert "by_status" in stats
    assert "by_priority" in stats
    assert "overdue_count" in stats
    assert "due_today_count" in stats
    assert "upcoming_count" in stats

    # New contract: analysis with source
    assert "analysis" in body
    analysis = body["analysis"]
    assert "text" in analysis
    assert analysis["source"] == "fallback"  # AI is disabled in tests

    # Must always have generated_at
    assert "generated_at" in body


def test_summary_with_tasks_shows_correct_stats(client):
    """Create tasks, then verify summary stats are accurate."""
    now = datetime.now(timezone.utc)

    # Create a mix of tasks
    client.post("/api/tasks", json={
        "title": "Overdue task",
        "status": "pending",
        "priority": "high",
        "due_date": (now - timedelta(days=2)).isoformat(),
    })
    client.post("/api/tasks", json={
        "title": "Due today task",
        "status": "pending",
        "priority": "medium",
        "due_date": now.isoformat(),
    })
    client.post("/api/tasks", json={
        "title": "Future task",
        "status": "in_progress",
        "priority": "low",
        "due_date": (now + timedelta(days=3)).isoformat(),
    })

    response = client.get("/api/summary/today")
    assert response.status_code == 200
    body = response.json()

    assert body["stats"]["total_tasks"] >= 3
    assert body["analysis"]["source"] == "fallback"
    assert len(body["analysis"]["text"]) > 0
