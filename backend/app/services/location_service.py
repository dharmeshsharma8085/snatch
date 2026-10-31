from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.schemas.location import (
    LocationUpdate,
    LocationResponse
)


# Prototype storage: data server restart hone par clear ho jayega.
LAST_KNOWN_LOCATIONS: dict[UUID, LocationResponse] = {}

STALE_AFTER_MINUTES = 15
MAX_FUTURE_MINUTES = 5


def process_location_update(
    location: LocationUpdate
) -> LocationResponse:

    # 1. Check user consent
    if not location.consent_granted:
        raise PermissionError(
            "Location access requires user consent."
        )

    now = datetime.now(timezone.utc)
    captured_at = location.captured_at

    # 2. Reject timestamps too far in the future
    if captured_at > now + timedelta(
        minutes=MAX_FUTURE_MINUTES
    ):
        raise ValueError(
            "Location timestamp cannot be in the future."
        )

    # 3. Check whether location is stale
    age = now - captured_at

    if age > timedelta(minutes=STALE_AFTER_MINUTES):
        status = "stale"
        message = "Location received, but it may be outdated."
    else:
        status = "fresh"
        message = "Location received successfully."

    # 4. Build response
    response = LocationResponse(
        device_id=location.device_id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy_m=location.accuracy_m,
        captured_at=captured_at,
        status=status,
        message=message
    )

    # 5. Save last-known location
    LAST_KNOWN_LOCATIONS[location.device_id] = response

    return response


def get_last_known_location(
    device_id: UUID
) -> LocationResponse | None:

    return LAST_KNOWN_LOCATIONS.get(device_id)