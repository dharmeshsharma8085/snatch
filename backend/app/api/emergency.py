from fastapi import APIRouter

from app.schemas.emergency import (
    EmergencyRequest,
    EmergencyResponse
)

from app.services.emergency_service import (
    process_emergency
)


router = APIRouter(
    prefix="/api/v1/emergency",
    tags=["Emergency Response"]
)


@router.post("/", response_model=EmergencyResponse)
def create_emergency(
    request: EmergencyRequest
):
    return process_emergency(request)