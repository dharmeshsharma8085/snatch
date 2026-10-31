from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EvidenceCreate(BaseModel):

    device_id: UUID

    evidence_type: Literal[
        "device_event",
        "location_update",
        "user_report",
        "system_log"
    ]

    source: Literal[
        "android",
        "ios",
        "backend",
        "simulator"
    ]

    recorded_at: datetime

    payload: dict[str, Any] = Field(
        default_factory=dict
    )

    @field_validator("recorded_at")
    @classmethod
    def validate_timestamp(cls, value):

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Timestamp must include timezone information"
            )

        return value


class EvidenceResponse(BaseModel):

    evidence_id: UUID = Field(
        default_factory=uuid4
    )

    device_id: UUID

    evidence_type: str

    source: str

    recorded_at: datetime

    payload: dict[str, Any]

    sha256_hash: str

    integrity_status: str