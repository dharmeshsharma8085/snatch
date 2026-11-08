from uuid import UUID

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.emergency import Emergency
from app.models.trusted_contact import TrustedContact
from app.models.notification import NotificationDelivery


def queue_emergency_notifications(
    emergency_id: UUID,
    user_id: UUID,
):
    with SessionLocal() as db:

        emergency = db.scalar(
            select(Emergency).where(
                Emergency.emergency_id == str(emergency_id),
                Emergency.user_id == str(user_id),
            )
        )

        if emergency is None:
            raise PermissionError("Emergency record not found.")

        if (
            emergency.status != "approved_pending_delivery"
            or not emergency.owner_approved
        ):
            raise ValueError(
                "Emergency must be approved before queueing notifications."
            )

        contact_ids = emergency.trusted_contact_ids or []

        if not contact_ids:
            raise ValueError("No trusted contacts selected.")

        contacts = db.scalars(
            select(TrustedContact).where(
                TrustedContact.contact_id.in_(contact_ids),
                TrustedContact.user_id == str(user_id),
                TrustedContact.is_active.is_(True),
            )
        ).all()

        if len(contacts) != len(set(contact_ids)):
            raise ValueError(
                "One or more trusted contacts are no longer active."
            )

        created_count = 0

        for contact in contacts:

            existing = db.scalar(
                select(NotificationDelivery).where(
                    NotificationDelivery.emergency_id
                    == emergency.emergency_id,
                    NotificationDelivery.contact_id
                    == contact.contact_id,
                    NotificationDelivery.channel == "sms",
                )
            )

            if existing is not None:
                continue

            delivery = NotificationDelivery(
                emergency_id=emergency.emergency_id,
                contact_id=contact.contact_id,
                channel="sms",
                status="queued",
                attempt_count=0,
            )

            db.add(delivery)
            created_count += 1

        emergency.delivery_status = "queued"
        db.commit()

        return {
            "emergency_id": emergency.emergency_id,
            "delivery_status": emergency.delivery_status,
            "recipient_count": len(contacts),
            "queued_count": created_count,
            "message": "Notification records queued successfully.",
        }