
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.services.device_service import get_device
from app.schemas.workflow import (
    MultiAgentAnalyzeRequest,
    MultiAgentAnalyzeResponse,
)
from app.graph.workflow import snatch_graph


router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["Multi-Agent Workflow"],
)


def validate_device_payloads(request: MultiAgentAnalyzeRequest) -> None:
    """Ensure every supplied payload belongs to the event's device."""

    device_id = request.event.device_id

    payloads = {
        "battery": request.battery_data,
        "location": request.location_data,
        "evidence": request.evidence_data,
        "emergency": request.emergency_data,
    }

    for payload_name, payload in payloads.items():
        if payload is not None and payload.device_id != device_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{payload_name} device_id must match event device_id",
            )


@router.post(
    "/analyze",
    response_model=MultiAgentAnalyzeResponse,
)
async def analyze_multi_agent(
    request: MultiAgentAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    # 1. Validate nested payload device IDs.
    validate_device_payloads(request)

    # 2. Resolve device using authenticated ownership.
    authenticated_user_id = UUID(str(current_user.user_id))

    device = get_device(
        device_id=request.event.device_id,
        user_id=authenticated_user_id,
    )

    if device is None or not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active device not found",
        )

    # 3. Verify registered device platform.
    if device.platform != request.event.platform:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device platform mismatch",
        )

    if (
        request.battery_data is not None
        and request.battery_data.platform != device.platform
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Battery platform mismatch",
        )

    # 4. Never trust user_id supplied in the request body.
    event_data = request.event.model_dump(mode="json")
    event_data["user_id"] = str(authenticated_user_id)

    # 5. Prepare graph state.
    initial_state = {
        "event": event_data,
        "agent_trace": [],
        "errors": [],
    }

    if request.battery_data is not None:
        initial_state["battery_data"] = (
            request.battery_data.model_dump(mode="json")
        )

    if request.location_data is not None:
        initial_state["location_data"] = (
            request.location_data.model_dump(mode="json")
        )

    if request.evidence_data is not None:
        initial_state["evidence_data"] = (
            request.evidence_data.model_dump(mode="json")
        )

    if request.emergency_data is not None:
        initial_state["emergency_data"] = (
            request.emergency_data.model_dump(mode="json")
        )

    # 6. Execute workflow.
    try:
        result = await snatch_graph.ainvoke(initial_state)

        return MultiAgentAnalyzeResponse(
            risk_assessment=result.get("risk_assessment", {}),
            explanation=result.get("explanation", ""),
            next_action=result.get("next_action", ""),
            battery_assessment=result.get("battery_assessment"),
            location_assessment=result.get("location_assessment"),
            evidence_records=result.get("evidence_records", []),
            emergency_status=result.get("emergency_status"),
            agent_trace=result.get("agent_trace", []),
            errors=result.get("errors", []),
        )

    except Exception as exc:
        # Do not expose internal exception details to API clients.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multi-agent workflow execution failed",
        ) from exc
