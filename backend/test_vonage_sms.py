
from app.core.config import settings
from app.services.vonage_sms_provider import VonageSMSProvider


def main():
    if not settings.vonage_api_key or not settings.vonage_api_secret:
        print("Vonage credentials are missing.")
        return

    print("SNATCH - Manual Vonage SMS Test")
    recipient = input(
        "Enter your own verified phone number (E.164 format): "
    ).strip()

    if not recipient.startswith("+") or not recipient[1:].isdigit():
        print("Invalid phone number format.")
        return

    confirmation = input(
        "This sends a real test SMS. Type SEND to confirm: "
    ).strip()

    if confirmation != "SEND":
        print("Test cancelled. No SMS sent.")
        return

    provider = VonageSMSProvider(
        api_key=settings.vonage_api_key,
        api_secret=settings.vonage_api_secret,
        sender_id=settings.vonage_sender_id,
    )

    result = provider.send_sms(
        phone_number=recipient,
        message="SNATCH backend test: Vonage integration is working.",
    )

    if result.success:
        print("Vonage accepted the SMS request.")
        print("Message ID:", result.provider_message_id)
        print("Check your phone for delivery.")
    else:
        print("SMS request failed.")
        print("Reason:", result.error)


if __name__ == "__main__":
    main()
