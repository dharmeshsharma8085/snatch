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


def mock_device(platform="android", is_active=True):
    return SimpleNamespace(
        platform=platform,
        is_active=is_active,
    )


def build_payload(device_id, user_id=None, **extra):
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "event": {
            "event_id": str(uuid4()),
            "user_id": str(user_id or uuid4()),
            "device_id": str(device_id),
            "platform": "android",
            "event_type": "suspicious_activity",
            "signals": ["unusual_motion"],
            "occurred_at": now,
            "user_reported_theft": False,
        }
    }

    payload.update(extra)
    return payload


def mock_graph(monkeypatch, captured):
    async def fake_ainvoke(state):
        captured.update(state)
        return {
            "risk_assessment": {"score": 20},
            "explanation": "Test analysis",
            "next_action": "continue_monitoring",
            "agent_trace": [],
            "errors": [],
        }

    monkeypatch.setattr(
        "app.api.workflow.snatch_graph",
        SimpleNamespace(ainvoke=fake_ainvoke),
    )


def test_workflow_requires_authentication(client):
    response = client.post(
        "/api/v1/workflow/analyze",
        json=build_payload(uuid4()),
    )

    assert response.status_code == 401


def test_workflow_rejects_unowned_device(client, monkeypatch):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        lambda **kwargs: None,
    )

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=build_payload(device_id),
    )

    assert response.status_code == 404


def test_workflow_rejects_inactive_device(client, monkeypatch):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        lambda **kwargs: mock_device(is_active=False),
    )

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=build_payload(device_id),
    )

    assert response.status_code == 404


def test_workflow_rejects_platform_mismatch(client, monkeypatch):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        lambda **kwargs: mock_device(platform="ios"),
    )

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=build_payload(device_id),
    )

    assert response.status_code == 409


def test_workflow_rejects_battery_platform_mismatch(client, monkeypatch):
    user_id = uuid4()
    device_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        lambda **kwargs: mock_device(platform="android"),
    )

    payload = build_payload(
        device_id,
        battery_data={
            "device_id": str(device_id),
            "battery_level": 80,
            "is_charging": False,
            "captured_at": now,
            "platform": "ios",
        },
    )

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=payload,
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "field,payload_factory",
    [
        (
            "battery_data",
            lambda device_id, now: {
                "device_id": str(uuid4()),
                "battery_level": 80,
                "is_charging": False,
                "captured_at": now,
                "platform": "android",
            },
        ),
        (
            "location_data",
            lambda device_id, now: {
                "device_id": str(uuid4()),
                "latitude": 28.6,
                "longitude": 77.2,
                "accuracy_m": 10,
                "captured_at": now,
                "consent_granted": True,
            },
        ),
        (
            "evidence_data",
            lambda device_id, now: {
                "device_id": str(uuid4()),
                "evidence_type": "device_event",
                "source": "android",
                "recorded_at": now,
                "payload": {},
            },
        ),
        (
            "emergency_data",
            lambda device_id, now: {
                "device_id": str(uuid4()),
                "incident_id": str(uuid4()),
                "trigger_reason": "Test emergency",
                "trusted_contact_ids": [],
            },
        ),
    ],
)
def test_workflow_rejects_nested_device_mismatch(
    client,
    monkeypatch,
    field,
    payload_factory,
):
    user_id = uuid4()
    device_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        lambda **kwargs: mock_device(),
    )

    payload = build_payload(
        device_id,
        **{field: payload_factory(device_id, now)},
    )

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=payload,
    )

    assert response.status_code == 422


def test_workflow_overwrites_forged_user_id(client, monkeypatch):
    authenticated_user_id = uuid4()
    forged_user_id = uuid4()
    device_id = uuid4()

    authenticate_as(authenticated_user_id)

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        lambda **kwargs: mock_device(),
    )

    captured = {}
    mock_graph(monkeypatch, captured)

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=build_payload(
            device_id,
            user_id=forged_user_id,
        ),
    )

    assert response.status_code == 200
    assert captured["event"]["user_id"] == str(authenticated_user_id)
    assert captured["event"]["user_id"] != str(forged_user_id)


def test_workflow_passes_authenticated_device_to_service(
    client,
    monkeypatch,
):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    captured = {}

    def fake_get_device(**kwargs):
        captured.update(kwargs)
        return mock_device()

    monkeypatch.setattr(
        "app.api.workflow.get_device",
        fake_get_device,
    )

    graph_state = {}
    mock_graph(monkeypatch, graph_state)

    response = client.post(
        "/api/v1/workflow/analyze",
        headers={"Authorization": "Bearer test-token"},
        json=build_payload(device_id),
    )

    assert response.status_code == 200
    assert captured["device_id"] == device_id
    assert captured["user_id"] == user_id
