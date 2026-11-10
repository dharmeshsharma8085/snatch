
import pytest

from app.models.notification import NotificationDelivery
from app.services.delivery_receipt_service import (
    process_delivery_receipt,
)


def test_delivery_receipt_unknown_message(test_db, monkeypatch):
    from app.services import delivery_receipt_service

    monkeypatch.setattr(
        delivery_receipt_service,
        "SessionLocal",
        test_db,
    )

    result = process_delivery_receipt(
        message_id="unknown-message",
        status="delivered",
    )

    assert result["updated"] is False
    assert result["message"] == "Notification not found."


def test_invalid_delivery_status():
    with pytest.raises(ValueError):
        process_delivery_receipt(
            message_id="test-message",
            status="unknown",
        )


def test_delivered_receipt(test_db, monkeypatch):
    from app.services import delivery_receipt_service

    monkeypatch.setattr(
        delivery_receipt_service,
        "SessionLocal",
        test_db,
    )

    message_id = "vonage-test-delivered"

    with test_db() as db:
        notification = NotificationDelivery(
            emergency_id="missing-emergency",
            contact_id="missing-contact",
            channel="sms",
            status="submitted",
            provider_message_id=message_id,
            provider_status="accepted",
        )
        db.add(notification)
        db.commit()

    result = process_delivery_receipt(
        message_id=message_id,
        status="delivered",
    )

    assert result["updated"] is True
    assert result["delivery_status"] == "sent"
    assert result["provider_status"] == "delivered"

    with test_db() as db:
        saved = db.query(NotificationDelivery).filter_by(
            provider_message_id=message_id
        ).first()

        assert saved.status == "sent"
        assert saved.delivered_at is not None


def test_failed_receipt(test_db, monkeypatch):
    from app.services import delivery_receipt_service

    monkeypatch.setattr(
        delivery_receipt_service,
        "SessionLocal",
        test_db,
    )

    message_id = "vonage-test-failed"

    with test_db() as db:
        notification = NotificationDelivery(
            emergency_id="missing-emergency",
            contact_id="missing-contact",
            channel="sms",
            status="submitted",
            provider_message_id=message_id,
        )
        db.add(notification)
        db.commit()

    result = process_delivery_receipt(
        message_id=message_id,
        status="failed",
    )

    assert result["updated"] is True
    assert result["delivery_status"] == "failed"

    with test_db() as db:
        saved = db.query(NotificationDelivery).filter_by(
            provider_message_id=message_id
        ).first()

        assert saved.status == "failed"
        assert saved.delivered_at is None



def test_duplicate_delivery_receipt(test_db, monkeypatch):
    from app.services import delivery_receipt_service

    monkeypatch.setattr(
        delivery_receipt_service,
        "SessionLocal",
        test_db,
    )

    message_id = "vonage-duplicate-test"

    with test_db() as db:
        db.add(
            NotificationDelivery(
                emergency_id="missing-emergency",
                contact_id="missing-contact",
                channel="sms",
                status="submitted",
                provider_message_id=message_id,
            )
        )
        db.commit()

    first = process_delivery_receipt(
        message_id=message_id,
        status="delivered",
    )

    second = process_delivery_receipt(
        message_id=message_id,
        status="delivered",
    )

    assert first["updated"] is True
    assert second["updated"] is False