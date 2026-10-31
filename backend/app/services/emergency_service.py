from uuid import UUID

from app.schemas.emergency import (
    EmergencyRequest,
    EmergencyResponse
)


def process_emergency(
    request: EmergencyRequest
) -> EmergencyResponse:

    if not request.owner_approved:
        status = "pending_owner_approval"
        message = (
            "Emergency alert prepared. "
            "Waiting for owner approval."
        )
        recipient_count = 0

    else:
        status = "approved_pending_delivery"
        message = (
            "Emergency alert approved. "
            "Ready for authorized notification delivery."
        )
        recipient_count = len(
            request.trusted_contact_ids
        )

    return EmergencyResponse(
        incident_id=request.incident_id,
        device_id=request.device_id,
        status=status,
        message=message,
        recipient_count=recipient_count
    )