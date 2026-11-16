
import time
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.database.database import SessionLocal
from app.models.webhook_nonce import WebhookNonce


MAX_TIMESTAMP_AGE_SECONDS = 300


def register_webhook_nonce(
    timestamp: str,
    nonce: str,
) -> bool:
    """
    Validate callback timestamp and atomically register its nonce.
    Returns False for stale timestamps or previously used nonces.
    """

    if not timestamp or not nonce:
        return False

    if len(nonce) > 255:
        return False

    try:
        callback_timestamp = int(timestamp)
    except (ValueError, TypeError):
        return False

    now_epoch = int(time.time())

    if abs(now_epoch - callback_timestamp) > MAX_TIMESTAMP_AGE_SECONDS:
        return False

    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        try:
            # Remove expired nonce records.
            db.execute(
                delete(WebhookNonce).where(
                    WebhookNonce.expires_at < now
                )
            )

            db.add(
                WebhookNonce(
                    nonce=nonce,
                    created_at=now,
                    expires_at=now + timedelta(
                        seconds=MAX_TIMESTAMP_AGE_SECONDS
                    ),
                )
            )

            db.commit()
            return True

        except IntegrityError:
            db.rollback()
            return False

        except Exception:
            db.rollback()
            raise
