from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field



class NotificationDeliveryItem(BaseModel):
    delivery_id: UUID
    contact_id: UUID
    channel: str
    status: Literal[
        "queued",
        "processing",
        "submitted",
        "sent",
        "failed",
        "delivery_unknown",
    ]

    attempt_count: int = Field(ge=0)
    next_attempt_at: datetime | None = None
    last_error: str | None = None

    provider_message_id: str | None = None
    provider_status: str | None = None
    delivered_at: datetime | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


class EmergencyNotificationStatusResponse(BaseModel):
    emergency_id: UUID

    delivery_status: Literal[
        "not_started",
        "ready",
        "queued",
        "sent",
        "partially_failed",
        "failed",
        "delivery_unknown",
    ]

    recipient_count: int = Field(ge=0)
    notifications: list[NotificationDeliveryItem]

    message: str
    
    
class NotificationQueueResponse(BaseModel):
    emergency_id: UUID
    delivery_status: Literal["queued"]
    recipient_count: int = Field(ge=0)
    queued_count: int = Field(ge=0)
    message: str