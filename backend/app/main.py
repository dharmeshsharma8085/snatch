from app.api.evidence import router as evidence_router
from fastapi import FastAPI, HTTPException
from app.api.emergency import router as emergency_router
from app.core.config import settings
from app.api.battery import router as battery_router
from app.api.workflow import router as workflow_router
from app.api.incidents import router as incidents_router
from app.schemas.events import (
    DeviceEvent,
    AnalysisResponse,
    RiskAssessmentResponse
)

from app.api.devices import router as devices_router




from app.graph.workflow import snatch_graph
from app.api.auth import router as auth_router

app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic smartphone protection "
        "and emergency response platform"
    ),
    version="0.1.0"
)

app.include_router(evidence_router)

app.include_router(emergency_router)
app.include_router(battery_router)
app.include_router(workflow_router)
app.include_router(incidents_router)
app.include_router(auth_router)
app.include_router(devices_router)




@app.get("/")
async def root():

    return {
        "application": "SNATCH",
        "message": "Device protection system is running",
        "status": "operational"
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "SNATCH Backend"
    }


@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse
)
async def analyze_device_event(
    event: DeviceEvent
):

    try:

        initial_state = {
            "event": event.model_dump(mode="json"),
            "agent_trace": [],
            "errors": []
        }

        result = await snatch_graph.ainvoke(
            initial_state
        )

        assessment = result["risk_assessment"]

        return AnalysisResponse(
            event_id=event.event_id,

            risk_assessment=RiskAssessmentResponse(
                score=assessment["score"],
                level=assessment["level"],
                confidence=assessment["confidence"],
                signals=assessment["signals"],
                explanation=result["explanation"],
                recommended_action=(
                    assessment["recommended_action"]
                )
            ),

            next_action=result["next_action"],

            agent_trace=result["agent_trace"],

            openai_used=result.get("openai_used", False)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"SNATCH workflow failed: {str(error)}"
        )
