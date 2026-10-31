
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


SignalType = Literal[
    "unusual_motion",
    "connectivity_loss",
    "charger_disconnected",
    "location_anomaly",
    "critical_battery",
    "user_reported_theft"
]


class DeviceEvent(BaseModel):
    event_id: UUID
    user_id: UUID
    device_id: UUID

    platform: Literal[
        "android",
        "ios",
        "simulator"
    ] = "simulator"

    event_type: str

    signals: list[SignalType] = Field(
        default_factory=list
    )

    occurred_at: datetime

    user_reported_theft: bool = False


class RiskAssessmentResponse(BaseModel):
    score: int

    level: Literal[
        "normal",
        "low",
        "suspicious",
        "high",
        "critical"
    ]

    confidence: Literal[
        "low",
        "medium",
        "high"
    ]

    signals: list[str]
    explanation: str
    recommended_action: str


class AnalysisResponse(BaseModel):
    event_id: UUID
    risk_assessment: RiskAssessmentResponse
    next_action: str
    agent_trace: list[str]
    openai_used: bool
