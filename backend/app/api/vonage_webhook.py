
import hashlib
import hmac
import logging
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.services.delivery_receipt_service import (
    process_delivery_receipt,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks/vonage",
    tags=["Vonage Webhooks"],
)


def verify_sms_signature(
    params: dict[str, str],
    secret: str,
) -> bool:
    """
    Verify Vonage SMS API SHA-256 HMAC signature.
    """

    received_signature = params.get("sig")

    if not received_signature:
        return False

    signing_params = {
        key: value.replace("&", "_").replace("=", "_")
        for key, value in params.items()
        if key != "sig"
    }

    signing_string = "".join(
        f"&{key}={signing_params[key]}"
        for key in sorted(signing_params)
    )

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signing_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature.lower(),
        received_signature.lower(),
    )


@router.post("/delivery-receipt")
async def vonage_delivery_receipt(request: Request):
    """
    Public Vonage SMS delivery receipt webhook.
    """

    if not settings.vonage_signature_secret:
        logger.error("Vonage signature secret is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook verification is not configured.",
        )

    if request.query_params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameters are not supported.",
        )

    content_type = request.headers.get(
        "content-type", ""
    ).split(";")[0].strip().lower()

    if content_type != "application/x-www-form-urlencoded":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported webhook content type.",
        )

    body = await request.body()

    try:
        pairs = parse_qsl(
            body.decode("utf-8"),
            keep_blank_values=True,
            strict_parsing=True,
        )
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload.",
        )

    params = dict(pairs)

    # Reject duplicate parameters to avoid ambiguous signatures.
    if len(params) != len(pairs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate webhook parameters.",
        )

    if not params.get("timestamp") or not params.get("nonce"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing timestamp or nonce.",
        )

    if not verify_sms_signature(
        params,
        settings.vonage_signature_secret,
    ):
        logger.warning("Invalid Vonage SMS webhook signature.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    from app.services.webhook_replay_service import (
        register_webhook_nonce,
    )

    if not register_webhook_nonce(
        timestamp=params["timestamp"],
        nonce=params["nonce"],
    ):
        logger.warning("Rejected expired or replayed Vonage webhook.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Expired or previously used webhook nonce.",
        )
    message_id = params.get("messageId")
    provider_status = params.get("status")

    if not message_id or not provider_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing delivery receipt fields.",
        )

    try:
        result = process_delivery_receipt(
            message_id=message_id,
            status=provider_status,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported delivery receipt status.",
        )

    return {
        "received": True,
        "updated": result["updated"],
    }
