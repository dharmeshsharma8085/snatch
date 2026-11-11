from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def authenticate_as(user_id):
    fake_user = SimpleNamespace(user_id=str(user_id))
    app.dependency_overrides[get_current_user] = lambda: fake_user


def create_payload(device_id, user_id=None):
    return {
        "event_id": str(uuid4()),
        "user_id": str(user_id or uuid4()),
        "device_id": str(device_id),
        "platform": "android",
        "event_type": "suspicious_activity",
        "signals": ["unusual_motion"],
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "user_reported_theft": False,
    }


def mock_device(platform="android", is_active=True):
    return SimpleNamespace(
        platform=platform,
        is_active=is_active,
    )


def mock_graph(monkeypatch, captured):
    async def fake_ainvoke(state):
        captured.update(state)
        return {
            "risk_assessment": {
                "score": 20,
                "level": "low",
                "confidence": "high",
                "signals": ["unusual_motion"],
                "recommended_action": "continue_monitoring",
            },
            "explanation": "Test analysis",
            "next_action": "continue_monitoring",
            "agent_trace": ["Risk Intelligence Agent"],
            "openai_used": False,
        }

    monkeypatch.setattr(
        "app.main.snatch_graph",
        SimpleNamespace(ainvoke=fake_ainvoke),
    )


def test_legacy_analyze_requires_authentication(client):
    response = client.post(
        "/api/v1/analyze",
        json=create_payload(uuid4()),
    )

    assert response.status_code == 401


def test_legacy_analyze_rejects_unowned_device(client, monkeypatch):
    authenticate_as(uuid4())

    monkeypatch.setattr(
        "app.main.get_device",
        lambda **kwargs: None,
    )

    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(uuid4()),
    )

    assert response.status_code == 404


def test_legacy_analyze_rejects_inactive_device(client, monkeypatch):
    authenticate_as(uuid4())

    monkeypatch.setattr(
        "app.main.get_device",
        lambda **kwargs: mock_device(is_active=False),
    )

    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(uuid4()),
    )

    assert response.status_code == 404


def test_legacy_analyze_rejects_platform_mismatch(client, monkeypatch):
    authenticate_as(uuid4())

    monkeypatch.setattr(
        "app.main.get_device",
        lambda **kwargs: mock_device(platform="ios"),
    )

    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(uuid4()),
    )

    assert response.status_code == 409


def test_legacy_analyze_overwrites_forged_user_id(client, monkeypatch):
    authenticated_user_id = uuid4()
    forged_user_id = uuid4()
    device_id = uuid4()

    authenticate_as(authenticated_user_id)

    monkeypatch.setattr(
        "app.main.get_device",
        lambda **kwargs: mock_device(),
    )

    captured = {}
    mock_graph(monkeypatch, captured)

    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(device_id, forged_user_id),
    )

    assert response.status_code == 200
    assert captured["event"]["user_id"] == str(authenticated_user_id)
    assert captured["event"]["user_id"] != str(forged_user_id)


def test_legacy_analyze_uses_authenticated_user_for_device_lookup(
    client,
    monkeypatch,
):
    authenticated_user_id = uuid4()
    device_id = uuid4()
    captured_lookup = {}

    authenticate_as(authenticated_user_id)

    def fake_get_device(**kwargs):
        captured_lookup.update(kwargs)
        return mock_device()

    monkeypatch.setattr(
        "app.main.get_device",
        fake_get_device,
    )

    mock_graph(monkeypatch, {})

    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(device_id),
    )

    assert response.status_code == 200
    assert captured_lookup["user_id"] == authenticated_user_id
    assert captured_lookup["device_id"] == device_id
