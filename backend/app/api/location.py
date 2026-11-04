from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.location import LocationUpdate, LocationResponse
from app.services.location_service import (
    save_location_update,
    get_last_known_location,
)


router = APIRouter(
    prefix="/api/v1/location",
    tags=["Location Intelligence"],
)


@router.post(
    "/sync",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def sync_location(
    location: LocationUpdate,
    current_user=Depends(get_current_user),
):
    try:
        result = save_location_update(
            location=location,
            user_id=UUID(str(current_user.user_id)),
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Active device not found for this user.",
            )

        return result

    except PermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get(
    "/last-known/{device_id}",
    response_model=LocationResponse,
)
def last_known_location(
    device_id: UUID,
    current_user=Depends(get_current_user),
):
    result = get_last_known_location(
        device_id=device_id,
        user_id=UUID(str(current_user.user_id)),
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found for this user.",
        )

    return result