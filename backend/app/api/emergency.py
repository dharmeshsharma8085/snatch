from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.emergency import (
    EmergencyRequest,
    EmergencyApprovalRequest,
    EmergencyResponse,
)
from app.services.emergency_service import (
    process_emergency,
    approve_emergency,
)

router = APIRouter(
    prefix="/api/v1/emergency",
    tags=["Emergency Response"],
)


@router.post(
    "/",
    response_model=EmergencyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_emergency(
    request: EmergencyRequest,
    current_user=Depends(get_current_user),
):
    try:
        return process_emergency(
            request,
            UUID(str(current_user.user_id)),
        )

    except PermissionError:
        raise HTTPException(
            status_code=404,
            detail="Incident, device, or trusted contact not found.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


@router.post(
    "/{emergency_id}/approve",
    response_model=EmergencyResponse,
)
def approve_emergency_request(
    emergency_id: UUID,
    request: EmergencyApprovalRequest,
    current_user=Depends(get_current_user),
):
    try:
        return approve_emergency(
            emergency_id=emergency_id,
            user_id=UUID(str(current_user.user_id)),
            owner_confirmed=request.owner_confirmed,
        )

    except PermissionError:
        raise HTTPException(
            status_code=404,
            detail="Emergency record not found.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )