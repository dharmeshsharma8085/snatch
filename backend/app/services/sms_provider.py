
from dataclasses import dataclass
from typing import Protocol


@dataclass
class SMSResult:
    success: bool
    provider_message_id: str | None = None
    error: str | None = None


class SMSProvider(Protocol):
    def send_sms(self, phone_number: str, message: str) -> SMSResult:
        ...


class DisabledSMSProvider:
    def send_sms(self, phone_number: str, message: str) -> SMSResult:
        return SMSResult(
            success=False,
            error="SMS sending is disabled. No SMS was sent.",
        )


def get_sms_provider():
    from app.core.config import settings

    if not settings.sms_live_enabled:
        return DisabledSMSProvider()

    if not (
        settings.vonage_api_key
        and settings.vonage_api_secret
        and settings.vonage_sender_id
    ):
        return DisabledSMSProvider()

    from app.services.vonage_sms_provider import VonageSMSProvider

    return VonageSMSProvider(
        api_key=settings.vonage_api_key,
        api_secret=settings.vonage_api_secret,
        sender_id=settings.vonage_sender_id,
    )
