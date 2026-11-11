
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.schemas.battery import BatteryResponse


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    test_client = TestClient(app)

    yield test_client

    app.dependency_overrides.clear()


def authenticate_as(user_id):
    fake_user = SimpleNamespace(user_id=str(user_id))

    app.dependency_overrides[get_current_user] = (
        lambda: fake_user
    )


def create_payload(device_id, platform="android"):
    return {
        "device_id": str(device_id),
        "battery_level": 85,
        "is_charging": False,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
    }


def mock_device(
    device_id,
    platform="android",
    is_active=True,
):
    return SimpleNamespace(
        device_id=str(device_id),
        platform=platform,
        is_active=is_active,
    )


def mock_battery_response(device_id):
    return BatteryResponse(
        device_id=device_id,
        battery_level=85,
        is_charging=False,
        battery_status="normal",
        recommended_action="continue_normal_monitoring",
        location_sync_priority="normal",
        captured_at=datetime.now(timezone.utc),
    )


def test_battery_requires_authentication(client):
    response = client.post(
        "/api/v1/battery/",
        json=create_payload(uuid4()),
    )

    assert response.status_code == 401


def test_battery_rejects_device_not_owned_by_user(
    client,
    monkeypatch,
):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.battery.get_device",
        lambda **kwargs: None,
    )

    response = client.post(
        "/api/v1/battery/",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(device_id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active device not found"


def test_battery_rejects_inactive_device(
    client,
    monkeypatch,
):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.battery.get_device",
        lambda **kwargs: mock_device(
            device_id,
            is_active=False,
        ),
    )

    response = client.post(
        "/api/v1/battery/",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(device_id),
    )

    assert response.status_code == 404


def test_battery_rejects_platform_mismatch(
    client,
    monkeypatch,
):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.battery.get_device",
        lambda **kwargs: mock_device(
            device_id,
            platform="ios",
        ),
    )

    response = client.post(
        "/api/v1/battery/",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(
            device_id,
            platform="android",
        ),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Device platform mismatch"


def test_battery_accepts_valid_owner_request(
    client,
    monkeypatch,
):
    user_id = uuid4()
    device_id = uuid4()

    authenticate_as(user_id)

    monkeypatch.setattr(
        "app.api.battery.get_device",
        lambda **kwargs: mock_device(device_id),
    )

    monkeypatch.setattr(
        "app.api.battery.process_battery_update",
        lambda data: mock_battery_response(data.device_id),
    )

    response = client.post(
        "/api/v1/battery/",
        headers={"Authorization": "Bearer test-token"},
        json=create_payload(device_id),
    )

    assert response.status_code == 200
    assert response.json()["battery_status"] == "normal"
    assert response.json()["device_id"] == str(device_id)
