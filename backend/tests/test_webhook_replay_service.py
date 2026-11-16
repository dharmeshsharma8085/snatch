
import time

from app.models.webhook_nonce import WebhookNonce
from app.services import webhook_replay_service


def test_valid_webhook_nonce_accepted(test_db, monkeypatch):
    monkeypatch.setattr(
        webhook_replay_service,
        "SessionLocal",
        test_db,
    )

    timestamp = str(int(time.time()))

    result = webhook_replay_service.register_webhook_nonce(
        timestamp=timestamp,
        nonce="fresh-nonce-001",
    )

    assert result is True


def test_duplicate_nonce_rejected(test_db, monkeypatch):
    monkeypatch.setattr(
        webhook_replay_service,
        "SessionLocal",
        test_db,
    )

    timestamp = str(int(time.time()))
    nonce = "duplicate-nonce-001"

    first = webhook_replay_service.register_webhook_nonce(
        timestamp=timestamp,
        nonce=nonce,
    )
    second = webhook_replay_service.register_webhook_nonce(
        timestamp=timestamp,
        nonce=nonce,
    )

    assert first is True
    assert second is False


def test_expired_timestamp_rejected(test_db, monkeypatch):
    monkeypatch.setattr(
        webhook_replay_service,
        "SessionLocal",
        test_db,
    )

    old_timestamp = str(int(time.time()) - 600)

    result = webhook_replay_service.register_webhook_nonce(
        timestamp=old_timestamp,
        nonce="expired-nonce-001",
    )

    assert result is False


def test_invalid_timestamp_rejected(test_db, monkeypatch):
    monkeypatch.setattr(
        webhook_replay_service,
        "SessionLocal",
        test_db,
    )

    result = webhook_replay_service.register_webhook_nonce(
        timestamp="invalid-timestamp",
        nonce="invalid-nonce-001",
    )

    assert result is False


def test_missing_nonce_rejected(test_db, monkeypatch):
    monkeypatch.setattr(
        webhook_replay_service,
        "SessionLocal",
        test_db,
    )

    result = webhook_replay_service.register_webhook_nonce(
        timestamp=str(int(time.time())),
        nonce="",
    )

    assert result is False
