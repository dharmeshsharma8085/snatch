from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.models.user import User
from app.models.device import Device
from app.models.incident import Incident
from app.models.emergency import Emergency
from app.models.trusted_contact import TrustedContact
from app.models.notification import NotificationDelivery

from app.services.sms_provider import SMSResult
from app.workers import notification_worker


class FakeSMSProvider:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def send_sms(self, phone_number, message):
        self.calls.append((phone_number, message))
        return self.result


def create_notification_data(
    test_db,
    monkeypatch,
    approved=True,
    contact_active=True,
    attempt_count=0,
):
    monkeypatch.setattr(
        notification_worker,
        "SessionLocal",
        test_db,
    )

    monkeypatch.setattr(
        notification_worker.settings,
        "sms_live_enabled",
        True,
    )

    user_id = str(uuid4())
    device_id = str(uuid4())
    incident_id = str(uuid4())
    emergency_id = str(uuid4())
    contact_id = str(uuid4())
    delivery_id = str(uuid4())

    with test_db() as db:
        user = User(
            user_id=user_id,
            email=f"{user_id}@test.com",
            password_hash="test-hash",
            is_active=True,
        )

        device = Device(
            device_id=device_id,
            user_id=user_id,
            device_name="Worker Test Device",
            platform="android",
            is_active=True,
        )

        incident = Incident(
            incident_id=incident_id,
            user_id=user_id,
            device_id=device_id,
            risk_score=80,
            risk_level="high",
            trigger_reason="Simulated test incident",
            signals=["unusual_motion"],
            status="awaiting_owner_verification",
        )

        contact = TrustedContact(
            contact_id=contact_id,
            user_id=user_id,
            name="Test Contact",
            phone_number="+919876543210",
            is_active=contact_active,
        )

        emergency = Emergency(
            emergency_id=emergency_id,
            user_id=user_id,
            incident_id=incident_id,
            device_id=device_id,
            trigger_reason="Simulated emergency",
            trusted_contact_ids=[contact_id],
            owner_approved=approved,
            status=(
                "approved_pending_delivery"
                if approved
                else "pending_owner_approval"
            ),
            delivery_status="queued" if approved else "ready",
            recipient_count=1,
            attempt_count=0,
        )

        notification = NotificationDelivery(
            delivery_id=delivery_id,
            emergency_id=emergency_id,
            contact_id=contact_id,
            channel="sms",
            status="queued",
            attempt_count=attempt_count,
        )

        db.add_all([
            user,
            device,
            incident,
            contact,
            emergency,
            notification,
        ])
        db.commit()

    return delivery_id, emergency_id


def test_worker_skips_when_sms_disabled(
    monkeypatch,
):
    monkeypatch.setattr(
        notification_worker.settings,
        "sms_live_enabled",
        False,
    )

    result = notification_worker.process_notification_queue()

    assert result["skipped"] is True
    assert result["processed_count"] == 0


def test_worker_successful_submission(
    test_db,
    monkeypatch,
):
    delivery_id, emergency_id = create_notification_data(
        test_db,
        monkeypatch,
    )

    fake_provider = FakeSMSProvider(
        SMSResult(
            success=True,
            provider_message_id="fake-vonage-message-001",
        )
    )

    monkeypatch.setattr(
        notification_worker,
        "get_sms_provider",
        lambda: fake_provider,
    )

    result = notification_worker.process_notification_queue()

    assert result["processed_count"] == 1
    assert result["sent_count"] == 1
    assert len(fake_provider.calls) == 1

    with test_db() as db:
        saved = db.get(NotificationDelivery, delivery_id)
        emergency = db.get(Emergency, emergency_id)

        assert saved.status == "submitted"
        assert saved.provider_status == "accepted"
        assert saved.provider_message_id == "fake-vonage-message-001"
        assert saved.attempt_count == 1

        # Provider acceptance is not confirmed delivery.
        assert emergency.delivery_status == "queued"


def test_worker_does_not_send_without_owner_approval(
    test_db,
    monkeypatch,
):
    delivery_id, _ = create_notification_data(
        test_db,
        monkeypatch,
        approved=False,
    )

    fake_provider = FakeSMSProvider(
        SMSResult(success=True, provider_message_id="fake-id")
    )

    monkeypatch.setattr(
        notification_worker,
        "get_sms_provider",
        lambda: fake_provider,
    )

    result = notification_worker.process_notification_queue()

    assert result["processed_count"] == 0
    assert fake_provider.calls == []

    with test_db() as db:
        saved = db.get(NotificationDelivery, delivery_id)
        assert saved.status == "queued"
        assert saved.attempt_count == 0


def test_worker_schedules_retry_after_failure(
    test_db,
    monkeypatch,
):
    delivery_id, _ = create_notification_data(
        test_db,
        monkeypatch,
    )

    fake_provider = FakeSMSProvider(
        SMSResult(
            success=False,
            error="Simulated provider failure",
        )
    )

    monkeypatch.setattr(
        notification_worker,
        "get_sms_provider",
        lambda: fake_provider,
    )

    result = notification_worker.process_notification_queue()

    assert result["processed_count"] == 1
    assert result["failed_count"] == 0

    with test_db() as db:
        saved = db.get(NotificationDelivery, delivery_id)

        assert saved.status == "queued"
        assert saved.attempt_count == 1
        assert saved.next_attempt_at is not None
        assert saved.last_error == "Simulated provider failure"


def test_worker_marks_failed_after_max_attempts(
    test_db,
    monkeypatch,
):
    delivery_id, _ = create_notification_data(
        test_db,
        monkeypatch,
        attempt_count=2,
    )

    fake_provider = FakeSMSProvider(
        SMSResult(
            success=False,
            error="Simulated final failure",
        )
    )

    monkeypatch.setattr(
        notification_worker,
        "get_sms_provider",
        lambda: fake_provider,
    )

    result = notification_worker.process_notification_queue()

    assert result["processed_count"] == 1
    assert result["failed_count"] == 1

    with test_db() as db:
        saved = db.get(NotificationDelivery, delivery_id)

        assert saved.status == "failed"
        assert saved.attempt_count == 3
        assert saved.next_attempt_at is None


def test_worker_rejects_inactive_contact(
    test_db,
    monkeypatch,
):
    delivery_id, emergency_id = create_notification_data(
        test_db,
        monkeypatch,
        contact_active=False,
    )

    fake_provider = FakeSMSProvider(
        SMSResult(success=True, provider_message_id="fake-id")
    )

    monkeypatch.setattr(
        notification_worker,
        "get_sms_provider",
        lambda: fake_provider,
    )

    result = notification_worker.process_notification_queue()

    assert result["processed_count"] == 1
    assert result["failed_count"] == 1
    assert fake_provider.calls == []

    with test_db() as db:
        saved = db.get(NotificationDelivery, delivery_id)
        emergency = db.get(Emergency, emergency_id)

        assert saved.status == "failed"
        assert "Recipient validation failed" in saved.last_error
        assert emergency.delivery_status == "failed"

def test_claim_notifications_sets_processing_and_lease(
    test_db,
    monkeypatch,
):
    delivery_id, _ = create_notification_data(
        test_db,
        monkeypatch,
    )

    claimed_ids = notification_worker.claim_notifications()

    assert delivery_id in claimed_ids

    with test_db() as db:
        saved = db.get(NotificationDelivery, delivery_id)

        assert saved.status == "processing"
        assert saved.claimed_by is not None
        assert saved.claimed_at is not None
        assert saved.claim_expires_at is not None


def test_claim_notifications_does_not_claim_same_job_twice(
    test_db,
    monkeypatch,
):
    delivery_id, _ = create_notification_data(
        test_db,
        monkeypatch,
    )

    first_claim = notification_worker.claim_notifications()
    second_claim = notification_worker.claim_notifications()

    assert delivery_id in first_claim
    assert delivery_id not in second_claim


def test_claim_notifications_only_claims_eligible_jobs(
    test_db,
    monkeypatch,
):
    delivery_id, _ = create_notification_data(
        test_db,
        monkeypatch,
    )

    with test_db() as db:
        notification = db.get(NotificationDelivery, delivery_id)
        notification.next_attempt_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=10)
        )
        db.commit()

    claimed_ids = notification_worker.claim_notifications()

    assert delivery_id not in claimed_ids
