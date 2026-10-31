from pydantic import BaseModel, Field

from app.schemas.events import DeviceEvent
from app.schemas.battery import BatteryUpdate
from app.schemas.location import LocationUpdate
from app.schemas.evidence import EvidenceCreate
from app.schemas.emergency import EmergencyRequest


class MultiAgentAnalyzeRequest(BaseModel):
    event: DeviceEvent

    battery_data: BatteryUpdate | None = None
    location_data: LocationUpdate | None = None
    evidence_data: EvidenceCreate | None = None
    emergency_data: EmergencyRequest | None = None


class MultiAgentAnalyzeResponse(BaseModel):
    risk_assessment: dict = Field(default_factory=dict)
    explanation: str = ""
    next_action: str = ""
    battery_assessment: dict | None = None
    location_assessment: dict | None = None
    evidence_records: list[dict] = Field(default_factory=list)
    emergency_status: dict | None = None
    agent_trace: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)