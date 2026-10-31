from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LocationUpdate(BaseModel):

    device_id: UUID

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )

    accuracy_m: float = Field(
        ge=0,
        le=100000
    )

    captured_at: datetime

    consent_granted: bool

    @field_validator("captured_at")
    @classmethod
    def validate_timestamp(cls, value):

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Timestamp must include timezone information"
            )

        return value


class LocationResponse(BaseModel):

    device_id: UUID

    latitude: float

    longitude: float

    accuracy_m: float

    captured_at: datetime

    status: str

    message: str