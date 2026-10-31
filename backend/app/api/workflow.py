from fastapi import APIRouter, HTTPException

from app.schemas.workflow import (
    MultiAgentAnalyzeRequest,
    MultiAgentAnalyzeResponse,
)
from app.graph.workflow import snatch_graph


router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["Multi-Agent Workflow"],
)


@router.post(
    "/analyze",
    response_model=MultiAgentAnalyzeResponse,
)
async def analyze_multi_agent(
    request: MultiAgentAnalyzeRequest,
):
    try:
        # Convert validated request data into JSON-compatible dictionaries
        initial_state = {
            "event": request.event.model_dump(mode="json"),
            "agent_trace": [],
            "errors": [],
        }

        # Add optional specialist inputs only when provided
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

        # Execute LangGraph workflow
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
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent workflow failed: {str(exc)}",
        ) from exc