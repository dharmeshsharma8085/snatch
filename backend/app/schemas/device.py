
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from uuid import UUID


class DeviceCreate(BaseModel):
    device_name: str = Field(
        min_length=2,
        max_length=100,
    )

    platform: Literal[
        "android",
        "ios",
        "simulator",
    ]


class DeviceResponse(BaseModel):
    device_id: UUID
    user_id: UUID
    device_name: str
    platform: str
    is_active: bool
    last_seen_at: datetime | None
    created_at: datetime


class DeviceHeartbeatResponse(BaseModel):
    device_id: UUID
    status: Literal["online"]
    last_seen_at: datetime
    message: str
