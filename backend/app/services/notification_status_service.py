from uuid import UUID

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.emergency import Emergency
from app.models.notification import NotificationDelivery
from app.schemas.notification import (
    EmergencyNotificationStatusResponse,
    NotificationDeliveryItem,
)


def get_emergency_notification_status(
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

        deliveries = db.scalars(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.emergency_id
                == str(emergency_id)
            )
            .order_by(NotificationDelivery.created_at.asc())
        ).all()

        notifications = [
            NotificationDeliveryItem.model_validate(item)
            for item in deliveries
        ]

        messages = {
            "not_started": "Notification delivery has not started.",
            "ready": "Emergency approved and ready for queueing.",
            "queued": "Notifications are queued or awaiting retry.",
            "sent": "Notifications have been sent.",
            "partially_failed": "Some notifications failed.",
            "failed": "All notification delivery attempts failed.",
        }

        return EmergencyNotificationStatusResponse(
            emergency_id=emergency.emergency_id,
            delivery_status=emergency.delivery_status,
            recipient_count=emergency.recipient_count,
            notifications=notifications,
            message=messages.get(
                emergency.delivery_status,
                "Notification status retrieved.",
            ),
        )