
from uuid import uuid4

import pytest

from app.models.user import User
from app.models.device import Device
from app.models.incident import Incident
from app.models.trusted_contact import TrustedContact
from app.schemas.emergency import EmergencyRequest
from app.services import emergency_service


def seed_owner(db, label):
    user_id = uuid4()
    device_id = uuid4()
    incident_id = uuid4()
    contact_id = uuid4()

    user = User(
        user_id=str(user_id),
        email=f"{label}-{user_id}@test.com",
        password_hash="test-hash",
        is_active=True,
    )

    device = Device(
        device_id=str(device_id),
        user_id=str(user_id),
        device_name=f"{label} Android",
        platform="android",
        is_active=True,
    )

    incident = Incident(
        incident_id=str(incident_id),
        user_id=str(user_id),
        device_id=str(device_id),
        risk_score=75,
        risk_level="high",
        trigger_reason="Multiple suspicious signals",
        signals=["unusual_motion"],
        status="awaiting_owner_verification",
    )

    contact = TrustedContact(
        contact_id=str(contact_id),
        user_id=str(user_id),
        name=f"{label} Contact",
        phone_number=f"+919876543210",
        is_active=True,
    )

    db.add_all([user, device, incident, contact])
    db.commit()

    return {
        "user_id": user_id,
        "device_id": device_id,
        "incident_id": incident_id,
        "contact_id": contact_id,
    }


def make_request(owner):
    return EmergencyRequest(
        incident_id=owner["incident_id"],
        device_id=owner["device_id"],
        trigger_reason="Suspicious device activity",
        trusted_contact_ids=[owner["contact_id"]],
        owner_approved=False,
    )


def test_user_cannot_use_another_users_incident(test_db, monkeypatch):
    monkeypatch.setattr(emergency_service, "SessionLocal", test_db)

    with test_db() as db:
        user_a = seed_owner(db, "user-a")
        user_b = seed_owner(db, "user-b")

    request = make_request(user_b)

    with pytest.raises(PermissionError):
        emergency_service.process_emergency(
            request,
            user_a["user_id"],
        )


def test_user_cannot_use_another_users_device(test_db, monkeypatch):
    monkeypatch.setattr(emergency_service, "SessionLocal", test_db)

    with test_db() as db:
        user_a = seed_owner(db, "user-a")
        user_b = seed_owner(db, "user-b")

        incident_a = db.get(
            Incident,
            str(user_a["incident_id"]),
        )
        incident_a.device_id = str(user_b["device_id"])
        db.commit()

    request = make_request(user_a)
    request.device_id = user_b["device_id"]

    with pytest.raises(PermissionError):
        emergency_service.process_emergency(
            request,
            user_a["user_id"],
        )


def test_user_cannot_add_another_users_trusted_contact(
    test_db,
    monkeypatch,
):
    monkeypatch.setattr(emergency_service, "SessionLocal", test_db)

    with test_db() as db:
        user_a = seed_owner(db, "user-a")
        user_b = seed_owner(db, "user-b")

    request = make_request(user_a)
    request.trusted_contact_ids = [user_b["contact_id"]]

    with pytest.raises(PermissionError):
        emergency_service.process_emergency(
            request,
            user_a["user_id"],
        )


def test_user_cannot_approve_another_users_emergency(
    test_db,
    monkeypatch,
):
    monkeypatch.setattr(emergency_service, "SessionLocal", test_db)

    with test_db() as db:
        user_a = seed_owner(db, "user-a")
        user_b = seed_owner(db, "user-b")

    emergency = emergency_service.process_emergency(
        make_request(user_b),
        user_b["user_id"],
    )

    with pytest.raises(PermissionError):
        emergency_service.approve_emergency(
            emergency_id=emergency.emergency_id,
            user_id=user_a["user_id"],
            owner_confirmed=True,
        )

def test_duplicate_active_emergency_rejected(test_db, monkeypatch):
    monkeypatch.setattr(emergency_service, "SessionLocal", test_db)

    with test_db() as db:
        user = seed_owner(db, "duplicate-test")

    request = make_request(user)

    first = emergency_service.process_emergency(
        request, user["user_id"]
    )

    with pytest.raises(ValueError, match="already exists"):
        emergency_service.process_emergency(
            request, user["user_id"]
        )