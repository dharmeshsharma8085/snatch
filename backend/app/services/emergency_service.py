
from uuid import UUID

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.emergency import Emergency
from app.models.incident import Incident
from app.models.device import Device
from app.models.trusted_contact import TrustedContact

from app.schemas.emergency import EmergencyResponse


def _to_response(record: Emergency) -> EmergencyResponse:
    if record.status == "pending_owner_approval":
        message = "Emergency prepared. Waiting for owner approval."
    elif record.status == "approved_pending_delivery":
        message = "Emergency approved. Ready for notification delivery."
    else:
        message = "Emergency request cancelled by owner."

    return EmergencyResponse(
        emergency_id=record.emergency_id,
        incident_id=record.incident_id,
        device_id=record.device_id,
        trigger_reason=record.trigger_reason,
        trusted_contact_ids=record.trusted_contact_ids,
        status=record.status,
        owner_approved=record.owner_approved,
        delivery_status=record.delivery_status,
        recipient_count=record.recipient_count,
        attempt_count=record.attempt_count,
        message=message,
        created_at=record.created_at,
    )


def process_emergency(
    request,
    user_id: UUID,
) -> EmergencyResponse:

    with SessionLocal() as db:

        user_id_str = str(user_id)
        incident_id = str(request.incident_id)
        device_id = str(request.device_id)

        # 1. Verify incident ownership
        incident = db.scalar(
            select(Incident).where(
                Incident.incident_id == incident_id,
                Incident.user_id == user_id_str,
            )
        )

        if incident is None:
            raise PermissionError("Incident not found.")

        if incident.status in ("cancelled", "closed"):
            raise ValueError("This incident cannot start an emergency.")

        # 2. Verify incident-device relationship
        if incident.device_id != device_id:
            raise ValueError("Device does not match the incident.")

        # 3. Verify active device ownership
        device = db.scalar(
            select(Device).where(
                Device.device_id == device_id,
                Device.user_id == user_id_str,
                Device.is_active.is_(True),
            )
        )

        if device is None:
            raise PermissionError("Active device not found.")

        # 4. Validate trusted contacts
        contact_ids = [str(item) for item in request.trusted_contact_ids]

        if len(contact_ids) != len(set(contact_ids)):
            raise ValueError("Duplicate trusted contact IDs are not allowed.")

        if contact_ids:
            contacts = db.scalars(
                select(TrustedContact).where(
                    TrustedContact.contact_id.in_(contact_ids),
                    TrustedContact.user_id == user_id_str,
                    TrustedContact.is_active.is_(True),
                )
            ).all()

            if len(contacts) != len(contact_ids):
                raise PermissionError(
                    "One or more trusted contacts are unavailable."
                )

        # 5. Create emergency pending owner approval
        emergency = Emergency(
            user_id=user_id_str,
            incident_id=incident_id,
            device_id=device_id,
            trigger_reason=request.trigger_reason,
            trusted_contact_ids=contact_ids,
            owner_approved=False,
            status="pending_owner_approval",
            delivery_status="not_started",
            recipient_count=len(contact_ids),
            attempt_count=0,
        )

        db.add(emergency)
        db.commit()
        db.refresh(emergency)

        return _to_response(emergency)


def approve_emergency(
    emergency_id: UUID,
    user_id: UUID,
    owner_confirmed: bool,
) -> EmergencyResponse:

    with SessionLocal() as db:

        emergency = db.scalar(
            select(Emergency).where(
                Emergency.emergency_id == str(emergency_id),
                Emergency.user_id == str(user_id),
            )
        )

        if emergency is None:
            raise PermissionError("Emergency not found.")

        if emergency.status != "pending_owner_approval":
            raise ValueError(
                "Emergency is not waiting for owner approval."
            )

        if owner_confirmed:
            if not emergency.trusted_contact_ids:
                raise ValueError(
                    "Add at least one active trusted contact before approval."
                )

            emergency.owner_approved = True
            emergency.status = "approved_pending_delivery"
            emergency.delivery_status = "ready"

        else:
            emergency.owner_approved = False
            emergency.status = "cancelled"
            emergency.delivery_status = "not_started"

        db.commit()
        db.refresh(emergency)

        return _to_response(emergency)
