from unittest.mock import patch
import hashlib
import hmac

from app.api.vonage_webhook import verify_sms_signature
from fastapi.testclient import TestClient

import pytest
from app.main import app
from app.core.config import settings
@pytest.fixture
def client():
    return TestClient(app)

def generate_test_signature(params, secret):
    signing_params = {
        key: value.replace("&", "_").replace("=", "_")
        for key, value in params.items()
        if key != "sig"
    }

    signing_string = "".join(
        f"&{key}={signing_params[key]}"
        for key in sorted(signing_params)
    )

    return hmac.new(
        secret.encode(),
        signing_string.encode(),
        hashlib.sha256,
    ).hexdigest()


def test_valid_signature():
    secret = "test-secret"
    params = {
        "messageId": "test-message-123",
        "status": "delivered",
    }

    params["sig"] = generate_test_signature(params, secret)

    assert verify_sms_signature(params, secret) is True


def test_invalid_signature():
    params = {
        "messageId": "test-message-123",
        "status": "delivered",
        "sig": "invalid-signature",
    }

    assert verify_sms_signature(params, "test-secret") is False


def test_tampered_payload_rejected():
    secret = "test-secret"
    params = {
        "messageId": "test-message-123",
        "status": "delivered",
    }

    params["sig"] = generate_test_signature(params, secret)
    params["status"] = "failed"

    assert verify_sms_signature(params, secret) is False


def test_missing_signature_rejected():
    params = {
        "messageId": "test-message-123",
        "status": "delivered",
    }

    assert verify_sms_signature(params, "test-secret") is False



from urllib.parse import urlencode


def test_webhook_accepts_valid_signature(client, monkeypatch):
    secret = "test-secret"
    monkeypatch.setattr(
        settings,
        "vonage_signature_secret",
        secret,
    )

    params = {
        "messageId": "test-message-123",
        "status": "delivered",
    }
    params["sig"] = generate_test_signature(params, secret)

    with patch(
        "app.api.vonage_webhook.process_delivery_receipt"
    ) as mock_receipt:
        mock_receipt.return_value = {"updated": True}

        response = client.post(
            "/api/v1/webhooks/vonage/delivery-receipt",
            content=urlencode(params),
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
        )

    assert response.status_code == 200
    assert response.json()["updated"] is True
    mock_receipt.assert_called_once_with(
        message_id="test-message-123",
        status="delivered",
    )


def test_webhook_rejects_invalid_signature(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "vonage_signature_secret",
        "test-secret",
    )

    params = {
        "messageId": "test-message-123",
        "status": "delivered",
        "sig": "invalid-signature",
    }

    response = client.post(
        "/api/v1/webhooks/vonage/delivery-receipt",
        content=urlencode(params),
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
    )

    assert response.status_code == 401


def test_webhook_rejects_duplicate_parameters(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "vonage_signature_secret",
        "test-secret",
    )

    response = client.post(
        "/api/v1/webhooks/vonage/delivery-receipt",
        content=(
            "messageId=one&messageId=two"
            "&status=delivered&sig=invalid"
        ),
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
    )

    assert response.status_code == 400


def test_webhook_rejects_missing_signature(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "vonage_signature_secret",
        "test-secret",
    )

    params = {
        "messageId": "test-message-123",
        "status": "delivered",
    }

    response = client.post(
        "/api/v1/webhooks/vonage/delivery-receipt",
        content=urlencode(params),
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
    )

    assert response.status_code == 401
