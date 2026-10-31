
from typing import TypedDict, Any


class SnatchState(TypedDict, total=False):

    # ==================================
    # DEVICE INFORMATION
    # ==================================

    event: dict[str, Any]

    # ==================================
    # RISK INTELLIGENCE
    # ==================================

    risk_assessment: dict[str, Any]

    explanation: str
    openai_used: bool

    # ==================================
    # BATTERY GUARDIAN
    # ==================================

    battery_data: dict[str, Any]

    battery_assessment: dict[str, Any]

    # ==================================
    # LOCATION INTELLIGENCE
    # ==================================

    location_data: dict[str, Any]

    location_assessment: dict[str, Any]

    # ==================================
    # EVIDENCE MANAGER
    # ==================================

    evidence_data: dict[str, Any]

    evidence_records: list[dict[str, Any]]

    # ==================================
    # EMERGENCY RESPONSE
    # ==================================

    emergency_data: dict[str, Any]

    emergency_status: dict[str, Any]

    # ==================================
    # SUPERVISOR DECISION
    # ==================================

    next_action: str

    # ==================================
    # AGENT EXECUTION HISTORY
    # ==================================

    agent_trace: list[str]

    # ==================================
    # ERROR MANAGEMENT
    # ==================================

    errors: list[str]

    # ==================================
    # WORKFLOW CONTROL
    # ==================================

    workflow_status: str

    incident_id: str

    owner_approval_required: bool
