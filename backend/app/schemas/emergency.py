
from datetime import datetime
from typing import Literal
from uuid import UUID

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


class EmergencyApprovalRequest(BaseModel):
    owner_confirmed: bool


class EmergencyResponse(BaseModel):
    emergency_id: UUID 
    

    incident_id: UUID
    device_id: UUID

    trigger_reason: str

    trusted_contact_ids: list[UUID] = Field(
        default_factory=list
    )

    status: Literal[
        "pending_owner_approval",
        "approved_pending_delivery",
        "cancelled"
    ]

    owner_approved: bool

    delivery_status: Literal[
        "not_started",
        "ready",
        "queued",
        "sent",
        "partially_failed",
        "failed",
        "delivery_unknown",
    ]
    recipient_count: int
    attempt_count: int

    message: str

    created_at: datetime

    model_config = {"from_attributes": True}
