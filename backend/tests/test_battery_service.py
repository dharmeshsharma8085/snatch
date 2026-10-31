from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.battery import BatteryUpdate
from app.services.battery_service import process_battery_update


def create_battery_update(
    level,
    charging=False
):
    return BatteryUpdate(
        device_id=uuid4(),
        battery_level=level,
        is_charging=charging,
        captured_at=datetime.now(timezone.utc),
        platform="simulator"
    )


def test_normal_battery():
    result = process_battery_update(
        create_battery_update(85)
    )

    assert result.battery_status == "normal"
    assert result.location_sync_priority == "normal"


def test_low_battery():
    result = process_battery_update(
        create_battery_update(40)
    )

    assert result.battery_status == "low"
    assert result.location_sync_priority == "high"


def test_critical_battery():
    result = process_battery_update(
        create_battery_update(15)
    )

    assert result.battery_status == "critical"
    assert result.location_sync_priority == "urgent"


def test_critical_battery_while_charging():
    result = process_battery_update(
        create_battery_update(10, charging=True)
    )

    assert result.battery_status == "critical"
    assert result.recommended_action == "monitor_charging_and_battery"
    assert result.location_sync_priority == "urgent"


def test_battery_at_100_percent():
    result = process_battery_update(
        create_battery_update(100, charging=True)
    )

    assert result.battery_status == "normal"
    assert result.location_sync_priority == "normal"