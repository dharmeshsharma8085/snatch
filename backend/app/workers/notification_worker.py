
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import select, update, or_

from app.database.database import SessionLocal
from app.models.emergency import Emergency
from app.models.trusted_contact import TrustedContact
from app.models.notification import NotificationDelivery
from app.services.sms_provider import get_sms_provider
from app.core.config import settings


MAX_ATTEMPTS = 3
BATCH_SIZE = 20
CLAIM_LEASE_SECONDS = 300

RETRY_DELAYS = {
    1: 30,
    2: 60,
    3: 120,
}


def update_emergency_delivery_status(db, emergency_id):
    emergency = db.get(Emergency, emergency_id)

    if emergency is None:
        return

    deliveries = db.scalars(
        select(NotificationDelivery).where(
            NotificationDelivery.emergency_id == emergency_id
        )
    ).all()

    if not deliveries:
        return

    statuses = [item.status for item in deliveries]

    terminal = {"sent", "failed", "delivery_unknown"}

    if all(status == "sent" for status in statuses):
        emergency.delivery_status = "sent"

    elif all(status == "failed" for status in statuses):
        emergency.delivery_status = "failed"

    elif all(status in terminal for status in statuses):
        if "delivery_unknown" in statuses:
            emergency.delivery_status = "delivery_unknown"
        else:
            emergency.delivery_status = "partially_failed"

    else:
        emergency.delivery_status = "queued"


def recover_expired_claims():
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        expired = db.scalars(
            select(NotificationDelivery).where(
                NotificationDelivery.status == "processing",
                NotificationDelivery.claim_expires_at <= now,
            )
        ).all()

        emergency_ids = set()

        for item in expired:
            item.status = "delivery_unknown"
            item.last_error = (
                "Worker lease expired. Provider acceptance "
                "could not be confirmed. Manual reconciliation required."
            )
            item.claimed_by = None
            item.claimed_at = None
            item.claim_expires_at = None
            item.next_attempt_at = None

            emergency_ids.add(item.emergency_id)

        for emergency_id in emergency_ids:
            update_emergency_delivery_status(db, emergency_id)

        db.commit()

        return len(expired)


def claim_notifications():
    worker_id = f"notification-worker-{uuid4()}"
    now = datetime.now(timezone.utc)
    lease_expiry = now + timedelta(
        seconds=CLAIM_LEASE_SECONDS
    )

    with SessionLocal() as db:
        claimable_ids = (
            select(NotificationDelivery.delivery_id)
            .where(
                NotificationDelivery.status == "queued",
                or_(
                    NotificationDelivery.next_attempt_at.is_(None),
                    NotificationDelivery.next_attempt_at <= now,
                ),
            )
            .order_by(
                NotificationDelivery.created_at,
                NotificationDelivery.delivery_id,
            )
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )

        statement = (
            update(NotificationDelivery)
            .where(
                NotificationDelivery.delivery_id.in_(claimable_ids)
            )
            .values(
                status="processing",
                claimed_by=worker_id,
                claimed_at=now,
                claim_expires_at=lease_expiry,
            )
            .returning(NotificationDelivery.delivery_id)
        )

        claimed_ids = list(db.scalars(statement).all())

        db.commit()

        return claimed_ids


def process_notification_queue():

    if not settings.sms_live_enabled:
        return {
            "processed_count": 0,
            "sent_count": 0,
            "failed_count": 0,
            "unknown_count": 0,
            "recovered_count": 0,
            "max_attempts": MAX_ATTEMPTS,
            "skipped": True,
            "message": "SMS is disabled. Notification queue remains untouched.",
        }

    recovered_count = recover_expired_claims()
    claimed_ids = claim_notifications()

    processed_count = 0
    sent_count = 0
    failed_count = 0
    unknown_count = 0

    provider = get_sms_provider()

    for delivery_id in claimed_ids:

        # Read and validate before contacting the provider.
        with SessionLocal() as db:
            notification = db.get(
                NotificationDelivery,
                delivery_id,
            )

            if notification is None:
                continue

            if notification.status != "processing":
                continue

            worker_id = notification.claimed_by
            emergency = db.get(
                Emergency,
                notification.emergency_id,
            )

            if (
                emergency is None
                or not emergency.owner_approved
                or emergency.status != "approved_pending_delivery"
                or emergency.delivery_status not in (
                    "queued",
                    "ready",
                )
            ):
                notification.status = "queued"
                notification.claimed_by = None
                notification.claimed_at = None
                notification.claim_expires_at = None
                db.commit()
                continue

            contact = db.get(
                TrustedContact,
                notification.contact_id,
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
                notification.claimed_by = None
                notification.claimed_at = None
                notification.claim_expires_at = None

                update_emergency_delivery_status(
                    db,
                    notification.emergency_id,
                )

                db.commit()

                processed_count += 1
                failed_count += 1
                continue

            phone_number = contact.phone_number
            emergency_id = notification.emergency_id

        # No database transaction or row lock is held
        # while making the external provider request.
        message = (
            "SNATCH emergency alert: The device owner has "
            "approved this notification. Please contact the "
            "owner directly. This alert does not confirm theft."
        )

        try:
            result = provider.send_sms(
                phone_number=phone_number,
                message=message,
            )
        except Exception:
            # A crash or unexpected provider exception can leave
            # the notification processing. Lease recovery will
            # conservatively classify it as delivery_unknown.
            continue

        now = datetime.now(timezone.utc)

        with SessionLocal() as db:
            notification = db.scalar(
                select(NotificationDelivery).where(
                    NotificationDelivery.delivery_id == delivery_id,
                    NotificationDelivery.status == "processing",
                    NotificationDelivery.claimed_by == worker_id,
                )
            )

            # Another recovery process may already have handled it.
            if notification is None:
                continue

            notification.attempt_count += 1
            processed_count += 1

            notification.claimed_by = None
            notification.claimed_at = None
            notification.claim_expires_at = None

            if result.outcome_unknown:
                notification.status = "delivery_unknown"
                notification.provider_status = "unknown"
                notification.last_error = (
                    result.error
                    or "Provider acceptance could not be confirmed."
                )
                notification.next_attempt_at = None
                unknown_count += 1

            elif result.success and result.provider_message_id:
                notification.status = "submitted"
                notification.provider_message_id = (
                    result.provider_message_id
                )
                notification.provider_status = "accepted"
                notification.last_error = None
                notification.next_attempt_at = None
                sent_count += 1

            elif result.success:
                notification.status = "delivery_unknown"
                notification.provider_status = "unknown"
                notification.last_error = (
                    "Provider accepted request without a message ID. "
                    "Manual reconciliation required."
                )
                notification.next_attempt_at = None
                unknown_count += 1

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

            update_emergency_delivery_status(
                db,
                emergency_id,
            )

            db.commit()

    return {
        "processed_count": processed_count,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "unknown_count": unknown_count,
        "recovered_count": recovered_count,
        "max_attempts": MAX_ATTEMPTS,
        "message": "Notification queue processing completed.",
    }
  