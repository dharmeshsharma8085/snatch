
from uuid import uuid4

from app.models.user import User
from app.models.device import Device
from app.models.incident import Incident
from app.models.trusted_contact import TrustedContact

from app.schemas.emergency import EmergencyRequest
from app.services import emergency_service


def create_test_data(test_db, monkeypatch):
    monkeypatch.setattr(emergency_service, "SessionLocal", test_db)

    user_id = uuid4()
    device_id = uuid4()
    incident_id = uuid4()

    contact_ids = [uuid4(), uuid4()]

    with test_db() as db:
        user = User(
            user_id=str(user_id),
            email=f"{user_id}@test.com",
            password_hash="test-hash",
            is_active=True,
        )

        device = Device(
            device_id=str(device_id),
            user_id=str(user_id),
            device_name="Test Android",
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
            signals=["unusual_motion", "connectivity_loss"],
            status="awaiting_owner_verification",
        )

        contacts = [
            TrustedContact(
                contact_id=str(contact_id),
                user_id=str(user_id),
                name=f"Test Contact {index + 1}",
                phone_number=f"+91987654321{index}",
                is_active=True,
            )
            for index, contact_id in enumerate(contact_ids)
        ]

        db.add_all([user, device, incident, *contacts])
        db.commit()

    request = EmergencyRequest(
        incident_id=incident_id,
        device_id=device_id,
        trigger_reason="Multiple suspicious device signals",
        trusted_contact_ids=contact_ids,
        owner_approved=False,
    )

    return request, user_id


def test_emergency_requires_owner_approval(test_db, monkeypatch):
    request, user_id = create_test_data(test_db, monkeypatch)

    result = emergency_service.process_emergency(request, user_id)

    assert result.status == "pending_owner_approval"
    assert result.owner_approved is False
    assert result.recipient_count == 2
    assert result.delivery_status == "not_started"


def test_approved_emergency(test_db, monkeypatch):
    request, user_id = create_test_data(test_db, monkeypatch)

    created = emergency_service.process_emergency(request, user_id)

    result = emergency_service.approve_emergency(
        emergency_id=created.emergency_id,
        user_id=user_id,
        owner_confirmed=True,
    )

    assert result.status == "approved_pending_delivery"
    assert result.owner_approved is True
    assert result.recipient_count == 2
    assert result.delivery_status == "ready"


def test_emergency_has_unique_id(test_db, monkeypatch):
    request, user_id = create_test_data(test_db, monkeypatch)

    result = emergency_service.process_emergency(request, user_id)

    assert result.emergency_id is not None


def test_incident_id_is_preserved(test_db, monkeypatch):
    request, user_id = create_test_data(test_db, monkeypatch)

    result = emergency_service.process_emergency(request, user_id)

    assert str(result.incident_id) == str(request.incident_id)


def test_device_id_is_preserved(test_db, monkeypatch):
    request, user_id = create_test_data(test_db, monkeypatch)

    result = emergency_service.process_emergency(request, user_id)

    assert str(result.device_id) == str(request.device_id)
