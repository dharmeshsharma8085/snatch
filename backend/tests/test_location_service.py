from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest

from app.schemas.location import LocationUpdate
from app.services.location_service import (
    process_location_update,
    get_last_known_location,
    LAST_KNOWN_LOCATIONS
)


@pytest.fixture(autouse=True)
def clear_locations():
    LAST_KNOWN_LOCATIONS.clear()


def create_location(
    consent=True,
    captured_at=None
):
    return LocationUpdate(
        device_id=uuid4(),
        latitude=28.6139,
        longitude=77.2090,
        accuracy_m=10,
        captured_at=captured_at or datetime.now(timezone.utc),
        consent_granted=consent
    )


def test_fresh_location():
    location = create_location()

    result = process_location_update(location)

    assert result.status == "fresh"


def test_location_without_consent():
    location = create_location(consent=False)

    with pytest.raises(PermissionError):
        process_location_update(location)


def test_stale_location():
    old_time = datetime.now(timezone.utc) - timedelta(minutes=30)

    location = create_location(captured_at=old_time)

    result = process_location_update(location)

    assert result.status == "stale"


def test_future_timestamp():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)

    location = create_location(captured_at=future_time)

    with pytest.raises(ValueError):
        process_location_update(location)


def test_get_last_known_location():
    location = create_location()

    process_location_update(location)

    result = get_last_known_location(location.device_id)

    assert result is not None
    assert result.device_id == location.device_id