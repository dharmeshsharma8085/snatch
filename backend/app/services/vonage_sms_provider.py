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

        # Validation happens before contacting Vonage.
        try:
            sms = self.build_message(phone_number, message)
        except ValueError as error:
            return SMSResult(
                success=False,
                error=str(error),
            )

        # Once the network request starts, an exception
        # may mean Vonage accepted the SMS but the response
        # was lost. Treat it as an unknown outcome.
        try:
            response = self.client.sms.send(sms)
        except Exception as error:
            logger.error(
                "Vonage request outcome unknown. Exception type: %s",
                type(error).__name__,
            )
            return SMSResult(
                success=False,
                error="Vonage request outcome is unknown. Manual reconciliation required.",
                outcome_unknown=True,
            )

        try:
            response_data = response.model_dump(exclude_unset=True)
            messages = response_data.get("messages", [])

            if not messages:
                return SMSResult(
                    success=False,
                    error="Vonage returned an empty response. Outcome unknown.",
                    outcome_unknown=True,
                )

            result = messages[0]

            if str(result.get("status")) == "0":
                message_id = result.get("message_id")

                if not message_id:
                    return SMSResult(
                        success=False,
                        error="Vonage accepted the request without a message ID.",
                        outcome_unknown=True,
                    )

                return SMSResult(
                    success=True,
                    provider_message_id=message_id,
                )

            return SMSResult(
                success=False,
                error=result.get(
                    "error_text",
                    "Vonage rejected the SMS request.",
                ),
            )

        except Exception as error:
            logger.error(
                "Vonage response could not be processed. Exception type: %s",
                type(error).__name__,
            )
            return SMSResult(
                success=False,
                error="Vonage response could not be verified. Outcome unknown.",
                outcome_unknown=True,
            )
