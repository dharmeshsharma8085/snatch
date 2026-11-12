
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import incidents
from app.core.security import get_current_user
from app.schemas.incident import IncidentResponse


@pytest.fixture
def setup_client(monkeypatch):
    app = FastAPI()
    app.include_router(incidents.router)

    user_id = uuid4()
    device_id = uuid4()
    incident_id = uuid4()

    current_user = SimpleNamespace(user_id=str(user_id))

    app.dependency_overrides[get_current_user] = (
        lambda: current_user
    )

    client = TestClient(app)

    def make_response(status="awaiting_owner_verification"):
        now = datetime.now(timezone.utc)

        return IncidentResponse(
            incident_id=incident_id,
            user_id=user_id,
            device_id=device_id,
            risk_score=75,
            risk_level="high",
            trigger_reason="Unusual device activity",
            signals=["unusual_motion"],
            status=status,
            created_at=now,
            updated_at=now,
        )

    return {
        "app": app,
        "client": client,
        "user_id": user_id,
        "device_id": device_id,
        "incident_id": incident_id,
        "make_response": make_response,
    }


def test_create_incident_success(setup_client, monkeypatch):
    data = setup_client
    expected = data["make_response"]()

    def mock_create_incident(data, user_id):
        assert user_id == data_user_id
        return expected

    data_user_id = data["user_id"]

    monkeypatch.setattr(
        incidents,
        "create_incident",
        mock_create_incident,
    )

    response = data["client"].post(
        "/api/v1/incidents/",
        json={
            "device_id": str(data["device_id"]),
            "risk_score": 75,
            "risk_level": "high",
            "trigger_reason": "Unusual device activity",
            "signals": ["unusual_motion"],
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "awaiting_owner_verification"


def test_create_incident_rejects_unowned_device(
    setup_client, monkeypatch
):
    data = setup_client

    def mock_create_incident(data, user_id):
        raise PermissionError()

    monkeypatch.setattr(
        incidents,
        "create_incident",
        mock_create_incident,
    )

    response = data["client"].post(
        "/api/v1/incidents/",
        json={
            "device_id": str(data["device_id"]),
            "risk_score": 75,
            "risk_level": "high",
            "trigger_reason": "Unusual device activity",
            "signals": ["unusual_motion"],
        },
    )

    assert response.status_code == 404


def test_get_incident_success(setup_client, monkeypatch):
    data = setup_client
    expected = data["make_response"]()

    def mock_get_incident(incident_id, user_id):
        assert incident_id == data["incident_id"]
        assert user_id == data["user_id"]
        return expected

    monkeypatch.setattr(
        incidents,
        "get_incident",
        mock_get_incident,
    )

    response = data["client"].get(
        f"/api/v1/incidents/{data['incident_id']}"
    )

    assert response.status_code == 200
    assert response.json()["incident_id"] == str(data["incident_id"])


def test_get_incident_not_found(setup_client, monkeypatch):
    data = setup_client

    monkeypatch.setattr(
        incidents,
        "get_incident",
        lambda incident_id, user_id: None,
    )

    response = data["client"].get(
        f"/api/v1/incidents/{data['incident_id']}"
    )

    assert response.status_code == 404


def test_verify_incident_success(setup_client, monkeypatch):
    data = setup_client
    expected = data["make_response"]("confirmed")

    def mock_verify_incident(
        incident_id, user_id, owner_confirmed
    ):
        assert user_id == data["user_id"]
        assert owner_confirmed is True
        return expected

    monkeypatch.setattr(
        incidents,
        "verify_incident",
        mock_verify_incident,
    )

    response = data["client"].post(
        f"/api/v1/incidents/{data['incident_id']}/verify",
        json={"owner_confirmed": True},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_verify_incident_not_found(setup_client, monkeypatch):
    data = setup_client

    monkeypatch.setattr(
        incidents,
        "verify_incident",
        lambda incident_id, user_id, owner_confirmed: None,
    )

    response = data["client"].post(
        f"/api/v1/incidents/{data['incident_id']}/verify",
        json={"owner_confirmed": True},
    )

    assert response.status_code == 404


def test_cancel_incident_success(setup_client, monkeypatch):
    data = setup_client
    expected = data["make_response"]("cancelled")

    def mock_cancel_incident(incident_id, user_id):
        assert user_id == data["user_id"]
        return expected

    monkeypatch.setattr(
        incidents,
        "cancel_incident",
        mock_cancel_incident,
    )

    response = data["client"].post(
        f"/api/v1/incidents/{data['incident_id']}/cancel"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_incident_not_found(setup_client, monkeypatch):
    data = setup_client

    monkeypatch.setattr(
        incidents,
        "cancel_incident",
        lambda incident_id, user_id: None,
    )

    response = data["client"].post(
        f"/api/v1/incidents/{data['incident_id']}/cancel"
    )

    assert response.status_code == 404



def test_incident_api_requires_authentication(setup_client):
    data = setup_client

    data["app"].dependency_overrides.pop(
        get_current_user,
        None,
    )

    response = data["client"].get(
        f"/api/v1/incidents/{data['incident_id']}"
    )

    assert response.status_code == 401
