
from app.graph.state import SnatchState

from app.services.battery_service import (
    process_battery_update
)

from app.services.location_service import (
    process_location_update
)

from app.schemas.battery import BatteryUpdate
from app.schemas.location import LocationUpdate

from app.schemas.evidence import EvidenceCreate
from app.services.evidence_service import create_evidence

from app.schemas.emergency import EmergencyRequest
from app.services.emergency_service import process_emergency


def prepare_verification(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    trace.append("Owner Verification Workflow")

    return {
        "next_action": "provisional_incident_and_owner_verification",
        "agent_trace": trace
    }


def continue_monitoring(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    trace.append("Monitoring Workflow")

    return {
        "next_action": "continue_monitoring",
        "agent_trace": trace
    }


def battery_guardian_node(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    errors = list(state.get("errors", []))

    battery_data = state.get("battery_data")

    if not battery_data:
        return {
            "errors": errors + ["Battery data unavailable"]
        }

    try:
        update = BatteryUpdate.model_validate(battery_data)
        result = process_battery_update(update)

        trace.append("Battery Guardian Agent")

        return {
            "battery_assessment": result.model_dump(mode="json"),
            "agent_trace": trace
        }

    except Exception as error:
        errors.append(f"Battery Guardian: {str(error)}")

        return {
            "errors": errors,
            "agent_trace": trace
        }


def location_intelligence_node(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    errors = list(state.get("errors", []))

    location_data = state.get("location_data")

    if not location_data:
        return {
            "errors": errors + ["Location data unavailable"]
        }

    try:
        update = LocationUpdate.model_validate(location_data)
        result = process_location_update(update)

        trace.append("Location Intelligence Agent")

        return {
            "location_assessment": result.model_dump(mode="json"),
            "agent_trace": trace
        }

    except Exception as error:
        errors.append(f"Location Intelligence: {str(error)}")

        return {
            "errors": errors,
            "agent_trace": trace
        }


def evidence_manager_node(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    errors = list(state.get("errors", []))

    evidence_data = state.get("evidence_data")

    if not evidence_data:
        return {
            "errors": errors + ["Evidence data unavailable"]
        }

    try:
        evidence = EvidenceCreate.model_validate(evidence_data)
        result = create_evidence(evidence)

        trace.append("Evidence Manager Agent")

        return {
            "evidence_records": [result.model_dump(mode="json")],
            "agent_trace": trace
        }

    except Exception as error:
        errors.append(f"Evidence Manager: {str(error)}")

        return {
            "errors": errors,
            "agent_trace": trace
        }


def emergency_response_node(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    errors = list(state.get("errors", []))

    emergency_data = state.get("emergency_data")

    if not emergency_data:
        return {
            "errors": errors + ["Emergency data unavailable"]
        }

    try:
        request = EmergencyRequest.model_validate(emergency_data)
        result = process_emergency(request)

        trace.append("Emergency Response Agent")

        return {
            "emergency_status": result.model_dump(mode="json"),
            "agent_trace": trace
        }

    except Exception as error:
        errors.append(f"Emergency Response: {str(error)}")

        return {
            "errors": errors,
            "agent_trace": trace
        }
