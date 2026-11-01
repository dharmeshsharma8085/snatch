
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceHeartbeatResponse,
)
from app.services.device_service import (
    register_device,
    get_user_devices,
    get_device,
    update_device_heartbeat,
    set_device_active_status,
)

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"],
)


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_new_device(
    data: DeviceCreate,
    current_user: User = Depends(get_current_user),
):
    device = register_device(
        data=data,
        user_id=UUID(current_user.user_id),
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This device installation is already registered to another user",
        )

    return device


@router.get(
    "/",
    response_model=list[DeviceResponse],
)
def list_registered_devices(
    current_user: User = Depends(get_current_user),
):
    return get_user_devices(
        user_id=UUID(current_user.user_id),
    )


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
)
def read_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
):
    device = get_device(
        device_id=device_id,
        user_id=UUID(current_user.user_id),
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return device




@router.post(
    "/{device_id}/heartbeat",
    response_model=DeviceHeartbeatResponse,
)
def device_heartbeat(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
):
    heartbeat = update_device_heartbeat(
        device_id=device_id,
        user_id=UUID(current_user.user_id),
    )

    if heartbeat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or inactive",
        )

    return heartbeat


@router.post(
    "/{device_id}/deactivate",
    response_model=DeviceResponse,
)
def deactivate_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
):
    device = set_device_active_status(
        device_id=device_id,
        user_id=UUID(current_user.user_id),
        is_active=False,
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return device


@router.post(
    "/{device_id}/reactivate",
    response_model=DeviceResponse,
)
def reactivate_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
):
    device = set_device_active_status(
        device_id=device_id,
        user_id=UUID(current_user.user_id),
        is_active=True,
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return device