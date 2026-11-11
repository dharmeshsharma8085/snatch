import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from uuid import UUID

from app.core.security import get_current_user
from app.models.user import User
from app.services.device_service import get_device

from app.api.location import router as location_router
from app.api.evidence import router as evidence_router
from app.api.emergency import router as emergency_router
from app.api.battery import router as battery_router
from app.api.workflow import router as workflow_router
from app.api.incidents import router as incidents_router
from app.api.devices import router as devices_router
from app.api.auth import router as auth_router

from app.core.config import settings

from app.schemas.events import (
    DeviceEvent,
    AnalysisResponse,
    RiskAssessmentResponse
)

from app.graph.workflow import snatch_graph
from app.workers.device_monitor import device_monitor_loop
from app.api.trusted_contacts import router as trusted_contacts_router
from app.api.notifications import router as notifications_router
from app.workers.notification_runner import notification_worker_loop
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Start background device monitoring
    monitor_task = asyncio.create_task(
        device_monitor_loop()
    )

    logger.info("SNATCH Device Monitor Started")

    # Start notification worker
    notification_stop_event = asyncio.Event()

    notification_task = asyncio.create_task(
        notification_worker_loop(
            notification_stop_event,
            poll_interval_seconds=15,
        )
    )

    logger.info("SNATCH Notification Worker Started")

    try:
        yield

    finally:
        # Stop notification worker gracefully
        notification_stop_event.set()

        try:
            await notification_task
        except asyncio.CancelledError:
            logger.info("SNATCH Notification Worker Stopped")

        # Stop device monitoring
        monitor_task.cancel()

        try:
            await monitor_task
        except asyncio.CancelledError:
            logger.info("SNATCH Device Monitor Stopped")

app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic smartphone protection "
        "and emergency response platform"
    ),
    version="0.1.0",
    lifespan=lifespan
)


# Register API routers
# Register API routers
app.include_router(evidence_router)
app.include_router(emergency_router)
app.include_router(battery_router)
app.include_router(workflow_router)
app.include_router(incidents_router)
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(location_router)
app.include_router(trusted_contacts_router)
app.include_router(notifications_router)



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
    event: DeviceEvent,
    current_user: User = Depends(get_current_user),
):
    # 1. Verify device ownership and active status.
    authenticated_user_id = UUID(str(current_user.user_id))

    device = get_device(
        device_id=event.device_id,
        user_id=authenticated_user_id,
    )

    if device is None or not device.is_active:
        raise HTTPException(
            status_code=404,
            detail="Active device not found",
        )

    # 2. Verify registered platform.
    if device.platform != event.platform:
        raise HTTPException(
            status_code=409,
            detail="Device platform mismatch",
        )

    # 3. Never trust user_id from request body.
    event_data = event.model_dump(mode="json")
    event_data["user_id"] = str(authenticated_user_id)

    try:
        initial_state = {
            "event": event_data,
            "agent_trace": [],
            "errors": [],
        }

        result = await snatch_graph.ainvoke(initial_state)

        assessment = result["risk_assessment"]

        return AnalysisResponse(
            event_id=event.event_id,
            risk_assessment=RiskAssessmentResponse(
                score=assessment["score"],
                level=assessment["level"],
                confidence=assessment["confidence"],
                signals=assessment["signals"],
                explanation=result["explanation"],
                recommended_action=assessment["recommended_action"],
            ),
            next_action=result["next_action"],
            agent_trace=result["agent_trace"],
            openai_used=result.get("openai_used", False),
        )

    except Exception as error:
        logger.exception("Legacy analysis workflow failed")

        raise HTTPException(
            status_code=500,
            detail="SNATCH workflow execution failed",
        ) from error
