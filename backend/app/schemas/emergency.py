from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EmergencyRequest(BaseModel):

    incident_id: UUID

    device_id: UUID

    trigger_reason: str = Field(
        min_length=3,
        max_length=500
    )

    trusted_contact_ids: list[UUID] = Field(
        default_factory=list,
        max_length=10
    )

    owner_approved: bool = False


class EmergencyResponse(BaseModel):

    emergency_id: UUID = Field(
        default_factory=uuid4
    )

    incident_id: UUID

    device_id: UUID

    status: Literal[
        "pending_owner_approval",
        "approved_pending_delivery"
    ]

    message: str

    recipient_count: int

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )