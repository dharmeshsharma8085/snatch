from fastapi import APIRouter

from app.schemas.battery import (
    BatteryUpdate,
    BatteryResponse
)

from app.services.battery_service import (
    process_battery_update
)


router = APIRouter(
    prefix="/api/v1/battery",
    tags=["Battery Guardian"]
)


@router.post("/", response_model=BatteryResponse)
def update_battery(data: BatteryUpdate):

    return process_battery_update(data)
