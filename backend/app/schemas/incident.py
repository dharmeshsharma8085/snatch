from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


IncidentStatus = Literal[
    "awaiting_owner_verification",
    "confirmed",
    "cancelled",
    "closed",
]




class IncidentCreate(BaseModel):
    device_id: UUID
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal[
        "normal",
        "low",
        "suspicious",
        "high",
        "critical",
    ]
    trigger_reason: str = Field(min_length=3, max_length=500)
    signals: list[str] = Field(default_factory=list)


class IncidentVerification(BaseModel):
    owner_confirmed: bool


class IncidentResponse(BaseModel):
    incident_id: UUID
    user_id: UUID
    device_id: UUID
    risk_score: int
    risk_level: str
    trigger_reason: str
    signals: list[str]
    status: Literal[
        "awaiting_owner_verification",
        "confirmed",
        "cancelled",
        "closed",
    ]
    created_at: object
    updated_at: object
