
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.battery import BatteryUpdate, BatteryResponse
from app.services.battery_service import process_battery_update
from app.services.device_service import get_device


router = APIRouter(
    prefix="/api/v1/battery",
    tags=["Battery Guardian"],
)


@router.post("/", response_model=BatteryResponse)
def update_battery(
    data: BatteryUpdate,
    current_user: User = Depends(get_current_user),
):
    device = get_device(
        device_id=data.device_id,
        user_id=UUID(current_user.user_id),
    )

    # Do not reveal whether another user's device exists.
    if device is None or not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active device not found",
        )

    if device.platform != data.platform:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device platform mismatch",
        )

    return process_battery_update(data)
