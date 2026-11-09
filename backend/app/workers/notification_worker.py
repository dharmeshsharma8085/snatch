
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.emergency import Emergency
from app.models.trusted_contact import TrustedContact
from app.models.notification import NotificationDelivery
from app.services.sms_provider import get_sms_provider
from app.core.config import settings


MAX_ATTEMPTS = 3

RETRY_DELAYS = {
    1: 30,
    2: 60,
    3: 120,
}

def process_notification_queue():

    if not settings.sms_live_enabled:
        return {
            "processed_count": 0,
            "sent_count": 0,
            "failed_count": 0,
            "max_attempts": MAX_ATTEMPTS,
            "skipped": True,
            "message": "SMS is disabled. Notification queue remains untouched.",
        }

    processed_count = 0
    sent_count = 0
    failed_count = 0

    provider = get_sms_provider()

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
            emergency = db.get(
                Emergency, notification.emergency_id
            )

            if (
                emergency is None
                or not emergency.owner_approved
                or emergency.status != "approved_pending_delivery"
                or emergency.delivery_status not in ("queued", "ready")
            ):
                continue

            contact = db.get(
                TrustedContact, notification.contact_id
            )

            if (
                contact is None
                or not contact.is_active
                or contact.user_id != emergency.user_id
                or contact.contact_id not in (
                    emergency.trusted_contact_ids or []
                )
            ):
                notification.status = "failed"
                notification.last_error = (
                    "Recipient validation failed. SMS not sent."
                )
                notification.next_attempt_at = None
                failed_count += 1
                processed_count += 1
                continue

            message = (
                "SNATCH emergency alert: The device owner has "
                "approved this notification. Please contact the "
                "owner directly. This alert does not confirm theft."
            )

            result = provider.send_sms(
                phone_number=contact.phone_number,
                message=message,
            )

            notification.attempt_count += 1
            processed_count += 1

            if result.success and result.provider_message_id:
                notification.status = "submitted"
                notification.provider_message_id = result.provider_message_id
                notification.provider_status = "accepted"
                notification.last_error = None
                notification.next_attempt_at = None
                sent_count += 1

            elif result.success:
                notification.status = "failed"
                notification.provider_status = "unknown"
                notification.last_error = (
                    "Provider accepted the request without returning a message ID."
                )
                notification.next_attempt_at = None
                failed_count += 1

            else:
                notification.last_error = (
                    result.error or "SMS provider request failed."
                )

                if notification.attempt_count >= MAX_ATTEMPTS:
                    notification.status = "failed"
                    notification.next_attempt_at = None
                    failed_count += 1
                else:
                    delay = RETRY_DELAYS[
                        notification.attempt_count
                    ]
                    notification.status = "queued"
                    notification.next_attempt_at = (
                        now + timedelta(seconds=delay)
                    )

        
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

            elif any(
                item.status in ("queued", "submitted")
                for item in deliveries
            ):
                emergency.delivery_status = "queued"

        db.commit()


    return {
        "processed_count": processed_count,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "max_attempts": MAX_ATTEMPTS,
        "message": "Notification queue processing completed.",
    }
