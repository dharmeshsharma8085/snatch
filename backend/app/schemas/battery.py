from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BatteryUpdate(BaseModel):

    device_id: UUID

    battery_level: int = Field(
        ge=0,
        le=100
    )

    is_charging: bool

    captured_at: datetime

    platform: Literal[
        "android",
        "ios",
        "simulator"
    ]

    @field_validator("captured_at")
    @classmethod
    def validate_timestamp(cls, value):

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Timestamp must include timezone information"
            )

        return value


class BatteryResponse(BaseModel):

    device_id: UUID

    battery_level: int

    is_charging: bool

    battery_status: Literal[
        "normal",
        "low",
        "critical"
    ]

    recommended_action: str

    location_sync_priority: Literal[
        "normal",
        "high",
        "urgent"
    ]

    captured_at: datetime