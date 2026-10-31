
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.incident import (
    IncidentCreate,
    IncidentVerification,
    IncidentResponse,
)
from app.services.incident_service import (
    create_incident,
    get_incident,
    verify_incident,
    cancel_incident,
)

router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["Incidents"],
)


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_incident(
    data: IncidentCreate,
    current_user: User = Depends(get_current_user),
):
    return create_incident(
        data=data,
        user_id=UUID(current_user.user_id),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def read_incident(
    incident_id: UUID,
    current_user: User = Depends(get_current_user),
):
    incident = get_incident(
        incident_id=incident_id,
        user_id=UUID(current_user.user_id),
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident


@router.post(
    "/{incident_id}/verify",
    response_model=IncidentResponse,
)
def verify_owner_incident(
    incident_id: UUID,
    data: IncidentVerification,
    current_user: User = Depends(get_current_user),
):
    incident = verify_incident(
        incident_id=incident_id,
        user_id=UUID(current_user.user_id),
        owner_confirmed=data.owner_confirmed,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident


@router.post(
    "/{incident_id}/cancel",
    response_model=IncidentResponse,
)
def cancel_owner_incident(
    incident_id: UUID,
    current_user: User = Depends(get_current_user),
):
    incident = cancel_incident(
        incident_id=incident_id,
        user_id=UUID(current_user.user_id),
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident
