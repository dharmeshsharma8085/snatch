
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.notification import NotificationDelivery
from app.models.emergency import Emergency


def process_delivery_receipt(message_id: str, status: str):
    normalized_status = status.strip().lower()

    allowed_statuses = {
        "delivered",
        "failed",
        "rejected",
        "expired",
        "accepted",
    }

    if normalized_status not in allowed_statuses:
        raise ValueError("Unsupported delivery receipt status.")

    with SessionLocal() as db:
        notification = db.scalar(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.provider_message_id == message_id
            )
            .with_for_update()
        )

        if notification is None:
            return {
                "updated": False,
                "message": "Notification not found.",
            }

        # Ignore duplicate or late receipts after a terminal state.
        if notification.status in ("sent", "failed"):
            return {
                "updated": False,
                "message": "Notification already has a final status.",
            }

        notification.provider_status = normalized_status

        if normalized_status == "delivered":
            notification.status = "sent"
            notification.delivered_at = datetime.now(timezone.utc)
            notification.last_error = None

        elif normalized_status in ("failed", "rejected", "expired"):
            notification.status = "failed"
            notification.last_error = (
                f"Vonage delivery status: {normalized_status}"
            )

        db.flush()

        emergency = db.get(Emergency, notification.emergency_id)

        if emergency is not None:
            deliveries = db.scalars(
                select(NotificationDelivery).where(
                    NotificationDelivery.emergency_id
                    == notification.emergency_id
                )
            ).all()

            if deliveries and all(
                item.status == "sent" for item in deliveries
            ):
                emergency.delivery_status = "sent"

            elif deliveries and all(
                item.status == "failed" for item in deliveries
            ):
                emergency.delivery_status = "failed"

            elif (
                any(item.status == "sent" for item in deliveries)
                or any(item.status == "failed" for item in deliveries)
            ) and all(
                item.status in ("sent", "failed")
                for item in deliveries
            ):
                emergency.delivery_status = "partially_failed"

            else:
                emergency.delivery_status = "queued"

        db.commit()

        return {
            "updated": True,
            "delivery_status": notification.status,
            "provider_status": notification.provider_status,
            "message": "Delivery receipt processed.",
        }
