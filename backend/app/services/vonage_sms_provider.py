import logging

from vonage import Auth, Vonage
from vonage_sms import SmsMessage

from app.services.sms_provider import SMSResult

logger = logging.getLogger(__name__)


class VonageSMSProvider:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        sender_id: str,
    ):
        self.client = Vonage(
            Auth(
                api_key=api_key,
                api_secret=api_secret,
            )
        )
        self.sender_id = sender_id
    def build_message(
        self,
        phone_number: str,
        message: str,
    ) -> SmsMessage:
        if not phone_number.strip():
            raise ValueError("Phone number cannot be empty.")

        if not message.strip():
            raise ValueError("Message cannot be empty.")

        return SmsMessage(
            to=phone_number,
            from_=self.sender_id,
            text=message,
        )
    
    
    
    def send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> SMSResult:
        try:
            sms = self.build_message(phone_number, message)
            response = self.client.sms.send(sms)

            response_data = response.model_dump(
                exclude_unset=True
            )

            messages = response_data.get("messages", [])

            if not messages:
                return SMSResult(
                    success=False,
                    error="Vonage returned an empty response.",
                )

            result = messages[0]

            if str(result.get("status")) == "0":
                return SMSResult(
                    success=True,
                    provider_message_id=result.get("message_id"),
                )

            return SMSResult(
                success=False,
                error=result.get(
                    "error_text",
                    "SMS delivery was not accepted by Vonage.",
                ),
            )

        except Exception:
            logger.exception("Vonage SMS request failed.")

            return SMSResult(
                success=False,
                error="Vonage SMS request failed.",
            )