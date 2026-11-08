from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.database.database import SessionLocal

from app.models.user import User
from app.models.device import Device
from app.models.incident import Incident
from app.models.emergency import Emergency
from app.models.trusted_contact import TrustedContact
from app.models.notification import NotificationDelivery
MAX_ATTEMPTS = 3

RETRY_DELAYS = {
    1: 30,
    2: 60,
    3: 120,
}


def process_notification_queue():
    processed_count = 0

    with SessionLocal() as db:
        now = datetime.now(timezone.utc)

        notifications = db.scalars(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.status == "queued",
                (
                    NotificationDelivery.next_attempt_at.is_(None)
                    | (NotificationDelivery.next_attempt_at <= now)
                ),
            )
            .with_for_update(skip_locked=True)
            .limit(20)
        ).all()

        for notification in notifications:
            notification.attempt_count += 1
            notification.last_error = (
                "SMS provider not configured. No real notification was sent."
            )

            if notification.attempt_count >= MAX_ATTEMPTS:
                notification.status = "failed"
                notification.next_attempt_at = None
            else:
                delay = RETRY_DELAYS[notification.attempt_count]

                notification.status = "queued"
                notification.next_attempt_at = (
                    now + timedelta(seconds=delay)
                )

            processed_count += 1

        db.flush()

        emergency_ids = {
            item.emergency_id for item in notifications
        }

        for emergency_id in emergency_ids:
            emergency = db.get(Emergency, emergency_id)

            if emergency is None:
                continue

            deliveries = db.scalars(
                select(NotificationDelivery).where(
                    NotificationDelivery.emergency_id == emergency_id
                )
            ).all()

            if deliveries and all(
                item.status == "failed" for item in deliveries
            ):
                emergency.delivery_status = "failed"
            else:
                emergency.delivery_status = "queued"

        db.commit()

    return {
        "processed_count": processed_count,
        "max_attempts": MAX_ATTEMPTS,
        "message": "Queue processing completed. No real SMS was sent.",
    }