
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.security import get_current_user
from app.database.database import Base
from app.models.user import User
from app.models.device import Device
from app.models.location import DeviceLocation
from app.services import location_service


@pytest.fixture
def location_api(monkeypatch):

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Device.__table__,
            DeviceLocation.__table__,
        ],
    )

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(
        location_service,
        "SessionLocal",
        TestSessionLocal,
    )

    owner_id = uuid4()
    attacker_id = uuid4()
    device_id = uuid4()

    with TestSessionLocal() as db:
        owner = User(
            user_id=str(owner_id),
            email="owner@test.com",
            password_hash="test-hash",
            is_active=True,
        )

        attacker = User(
            user_id=str(attacker_id),
            email="attacker@test.com",
            password_hash="test-hash",
            is_active=True,
        )

        device = Device(
            device_id=str(device_id),
            installation_id=str(uuid4()),
            user_id=str(owner_id),
            device_name="Location Test Device",
            platform="simulator",
            is_active=True,
            status="offline",
        )

        db.add_all([owner, attacker, device])
        db.commit()

    def authenticate_as(user_id):
        app.dependency_overrides[get_current_user] = (
            lambda: SimpleNamespace(user_id=str(user_id))
        )

    authenticate_as(owner_id)

    with TestClient(app) as client:
        yield {
            "client": client,
            "owner_id": owner_id,
            "attacker_id": attacker_id,
            "device_id": device_id,
            "session": TestSessionLocal,
            "authenticate_as": authenticate_as,
        }

    app.dependency_overrides.pop(get_current_user, None)
    engine.dispose()


def location_payload(device_id, consent=True):

    return {
        "device_id": str(device_id),
        "latitude": 28.6139,
        "longitude": 77.2090,
        "accuracy_m": 10,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "consent_granted": consent,
    }


def test_location_api_requires_authentication():

    app.dependency_overrides.pop(get_current_user, None)

    try:
        with TestClient(app) as client:

            response = client.get(
                f"/api/v1/location/last-known/{uuid4()}"
            )

            assert response.status_code in (401, 403)

            response = client.post(
                "/api/v1/location/sync",
                json=location_payload(uuid4()),
            )

            assert response.status_code in (401, 403)

    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_authenticated_user_can_sync_location(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    response = client.post(
        "/api/v1/location/sync",
        json=location_payload(device_id),
    )

    assert response.status_code == 201
    assert response.json()["device_id"] == str(device_id)
    assert response.json()["status"] == "fresh"


def test_user_cannot_sync_another_users_device(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    location_api["authenticate_as"](
        location_api["attacker_id"]
    )

    response = client.post(
        "/api/v1/location/sync",
        json=location_payload(device_id),
    )

    assert response.status_code == 404


def test_location_sync_requires_consent(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    response = client.post(
        "/api/v1/location/sync",
        json=location_payload(device_id, consent=False),
    )

    assert response.status_code == 403


def test_authenticated_user_can_get_last_known_location(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    sync_response = client.post(
        "/api/v1/location/sync",
        json=location_payload(device_id),
    )

    assert sync_response.status_code == 201

    response = client.get(
        f"/api/v1/location/last-known/{device_id}"
    )

    assert response.status_code == 200
    assert response.json()["device_id"] == str(device_id)


def test_user_cannot_get_another_users_location(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    sync_response = client.post(
        "/api/v1/location/sync",
        json=location_payload(device_id),
    )

    assert sync_response.status_code == 201

    location_api["authenticate_as"](
        location_api["attacker_id"]
    )

    response = client.get(
        f"/api/v1/location/last-known/{device_id}"
    )

    assert response.status_code == 404


def test_inactive_device_location_is_not_accessible(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    sync_response = client.post(
        "/api/v1/location/sync",
        json=location_payload(device_id),
    )

    assert sync_response.status_code == 201

    with location_api["session"]() as db:
        device = db.get(Device, str(device_id))
        device.is_active = False
        db.commit()

    response = client.get(
        f"/api/v1/location/last-known/{device_id}"
    )

    assert response.status_code == 404


def test_invalid_coordinates_are_rejected(location_api):

    client = location_api["client"]
    device_id = location_api["device_id"]

    payload = location_payload(device_id)
    payload["latitude"] = 120

    response = client.post(
        "/api/v1/location/sync",
        json=payload,
    )

    assert response.status_code == 422
