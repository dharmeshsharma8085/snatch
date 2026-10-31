from uuid import uuid4

from app.schemas.emergency import EmergencyRequest
from app.services.emergency_service import process_emergency


def create_emergency_request(approved=False):
    return EmergencyRequest(
        incident_id=uuid4(),
        device_id=uuid4(),
        trigger_reason="Multiple suspicious device signals",
        trusted_contact_ids=[
            uuid4(),
            uuid4()
        ],
        owner_approved=approved
    )


def test_emergency_requires_owner_approval():
    request = create_emergency_request()

    result = process_emergency(request)

    assert result.status == "pending_owner_approval"
    assert result.recipient_count == 0


def test_approved_emergency():
    request = create_emergency_request(approved=True)

    result = process_emergency(request)

    assert result.status == "approved_pending_delivery"
    assert result.recipient_count == 2


def test_emergency_has_unique_id():
    request = create_emergency_request()

    result = process_emergency(request)

    assert result.emergency_id is not None


def test_incident_id_is_preserved():
    request = create_emergency_request()

    result = process_emergency(request)

    assert result.incident_id == request.incident_id


def test_device_id_is_preserved():
    request = create_emergency_request()

    result = process_emergency(request)

    assert result.device_id == request.device_id