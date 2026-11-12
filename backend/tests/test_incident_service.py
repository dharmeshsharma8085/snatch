
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services import incident_service
from app.schemas.incident import IncidentCreate


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()
    db.__enter__.return_value = db
    db.__exit__.return_value = False

    monkeypatch.setattr(
        incident_service,
        "SessionLocal",
        lambda: db,
    )
    return db


@pytest.fixture
def ids():
    return {
        "user_id": uuid4(),
        "device_id": uuid4(),
        "incident_id": uuid4(),
    }


@pytest.fixture
def incident_data(ids):
    return IncidentCreate(
        device_id=ids["device_id"],
        risk_score=75,
        risk_level="high",
        trigger_reason="Unusual device activity",
        signals=["unusual_motion", "connectivity_loss"],
    )


def test_create_incident_success(
    mock_db, monkeypatch, ids, incident_data
):
    mock_db.scalar.return_value = SimpleNamespace(
        device_id=str(ids["device_id"]),
        user_id=str(ids["user_id"]),
        is_active=True,
    )

    expected = MagicMock()
    monkeypatch.setattr(
        incident_service,
        "to_response",
        lambda incident: expected,
    )

    result = incident_service.create_incident(
        data=incident_data,
        user_id=ids["user_id"],
    )

    assert result == expected
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    saved = mock_db.add.call_args.args[0]
    assert saved.user_id == str(ids["user_id"])
    assert saved.device_id == str(ids["device_id"])
    assert saved.status == "awaiting_owner_verification"


def test_create_incident_rejects_unowned_device(
    mock_db, ids, incident_data
):
    mock_db.scalar.return_value = None

    with pytest.raises(PermissionError):
        incident_service.create_incident(
            data=incident_data,
            user_id=ids["user_id"],
        )

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_create_incident_rolls_back_on_database_error(
    mock_db, ids, incident_data
):
    mock_db.scalar.return_value = SimpleNamespace(
        device_id=str(ids["device_id"]),
        user_id=str(ids["user_id"]),
        is_active=True,
    )

    mock_db.commit.side_effect = Exception("Database error")

    with pytest.raises(Exception):
        incident_service.create_incident(
            data=incident_data,
            user_id=ids["user_id"],
        )

    mock_db.rollback.assert_called_once()


def test_get_incident_success(mock_db, monkeypatch, ids):
    mock_db.scalar.return_value = SimpleNamespace()

    expected = MagicMock()
    monkeypatch.setattr(
        incident_service,
        "to_response",
        lambda incident: expected,
    )

    result = incident_service.get_incident(
        ids["incident_id"],
        ids["user_id"],
    )

    assert result == expected


def test_get_incident_not_found(mock_db, ids):
    mock_db.scalar.return_value = None

    result = incident_service.get_incident(
        ids["incident_id"],
        ids["user_id"],
    )

    assert result is None


@pytest.mark.parametrize(
    ("owner_confirmed", "expected_status"),
    [
        (True, "confirmed"),
        (False, "cancelled"),
    ],
)
def test_verify_incident_updates_status(
    mock_db,
    monkeypatch,
    ids,
    owner_confirmed,
    expected_status,
):
    incident = SimpleNamespace(
        status="awaiting_owner_verification",
        updated_at=None,
    )
    mock_db.scalar.return_value = incident

    expected = MagicMock()
    monkeypatch.setattr(
        incident_service,
        "to_response",
        lambda obj: expected,
    )

    result = incident_service.verify_incident(
        incident_id=ids["incident_id"],
        user_id=ids["user_id"],
        owner_confirmed=owner_confirmed,
    )

    assert incident.status == expected_status
    assert isinstance(incident.updated_at, datetime)
    assert result == expected
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_verify_incident_not_found(mock_db, ids):
    mock_db.scalar.return_value = None

    result = incident_service.verify_incident(
        incident_id=ids["incident_id"],
        user_id=ids["user_id"],
        owner_confirmed=True,
    )

    assert result is None
    mock_db.commit.assert_not_called()


def test_verify_incident_does_not_change_terminal_status(
    mock_db, monkeypatch, ids
):
    incident = SimpleNamespace(
        status="confirmed",
        updated_at=None,
    )
    mock_db.scalar.return_value = incident

    expected = MagicMock()
    monkeypatch.setattr(
        incident_service,
        "to_response",
        lambda obj: expected,
    )

    result = incident_service.verify_incident(
        incident_id=ids["incident_id"],
        user_id=ids["user_id"],
        owner_confirmed=False,
    )

    assert incident.status == "confirmed"
    assert incident.updated_at is None
    assert result == expected
    mock_db.commit.assert_not_called()


def test_cancel_incident_success(mock_db, monkeypatch, ids):
    incident = SimpleNamespace(
        status="awaiting_owner_verification",
        updated_at=None,
    )
    mock_db.scalar.return_value = incident

    expected = MagicMock()
    monkeypatch.setattr(
        incident_service,
        "to_response",
        lambda obj: expected,
    )

    result = incident_service.cancel_incident(
        incident_id=ids["incident_id"],
        user_id=ids["user_id"],
    )

    assert incident.status == "cancelled"
    assert isinstance(incident.updated_at, datetime)
    assert result == expected
    mock_db.commit.assert_called_once()


def test_cancel_incident_not_found(mock_db, ids):
    mock_db.scalar.return_value = None

    result = incident_service.cancel_incident(
        incident_id=ids["incident_id"],
        user_id=ids["user_id"],
    )

    assert result is None
    mock_db.commit.assert_not_called()


def test_cancel_incident_does_not_change_confirmed_status(
    mock_db, monkeypatch, ids
):
    incident = SimpleNamespace(
        status="confirmed",
        updated_at=None,
    )
    mock_db.scalar.return_value = incident

    expected = MagicMock()
    monkeypatch.setattr(
        incident_service,
        "to_response",
        lambda obj: expected,
    )

    result = incident_service.cancel_incident(
        incident_id=ids["incident_id"],
        user_id=ids["user_id"],
    )

    assert incident.status == "confirmed"
    assert incident.updated_at is None
    assert result == expected
    mock_db.commit.assert_not_called()
