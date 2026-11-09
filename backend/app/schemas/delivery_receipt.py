
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class VonageDeliveryReceipt(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    message_id: str = Field(alias="messageId")
    status: str
    error_code: str | None = Field(default=None, alias="err-code")
    message_timestamp: datetime | None = Field(
        default=None,
        alias="message-timestamp",
    )
    recipient: str | None = Field(default=None, alias="msisdn")
    sender: str | None = Field(default=None, alias="to")
    price: str | None = None
    network_code: str | None = Field(
        default=None,
        alias="network-code",
    )
