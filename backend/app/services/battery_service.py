from app.schemas.battery import (
    BatteryUpdate,
    BatteryResponse
)


def process_battery_update(
    data: BatteryUpdate
) -> BatteryResponse:

    battery = data.battery_level

    # Classify battery status
    if battery <= 20:
        status = "critical"

    elif battery <= 50:
        status = "low"

    else:
        status = "normal"

    # Determine recommended action
    if status == "critical":

        action = "prioritize_location_sync"
        priority = "urgent"

    elif status == "low":

        action = "prepare_location_sync"
        priority = "high"

    else:

        action = "continue_normal_monitoring"
        priority = "normal"

    # Charging devices still need accurate battery monitoring.
    if data.is_charging and status != "normal":
        action = "monitor_charging_and_battery"

    return BatteryResponse(
        device_id=data.device_id,
        battery_level=data.battery_level,
        is_charging=data.is_charging,
        battery_status=status,
        recommended_action=action,
        location_sync_priority=priority,
        captured_at=data.captured_at
    )