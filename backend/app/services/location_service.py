from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.device import Device
from app.models.location import DeviceLocation
from app.schemas.location import LocationUpdate, LocationResponse


STALE_AFTER_MINUTES = 15
MAX_FUTURE_MINUTES = 5


def process_location_update(
    location: LocationUpdate,
) -> LocationResponse:
    """
    Validate location data.
    Used by LangGraph and does not write to the database.
    """

    if not location.consent_granted:
        raise PermissionError(
            "Location access requires user consent."
        )

    now = datetime.now(timezone.utc)
    captured_at = location.captured_at

    if captured_at > now + timedelta(
        minutes=MAX_FUTURE_MINUTES
    ):
        raise ValueError(
            "Location timestamp cannot be in the future."
        )

    age = now - captured_at

    if age > timedelta(minutes=STALE_AFTER_MINUTES):
        status = "stale"
        message = "Location received, but it may be outdated."
    else:
        status = "fresh"
        message = "Location received successfully."

    return LocationResponse(
        device_id=location.device_id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy_m=location.accuracy_m,
        captured_at=location.captured_at,
        status=status,
        message=message,
    )


def save_location_update(
    location: LocationUpdate,
    user_id: UUID,
) -> LocationResponse | None:
    """
    Validate ownership and persist an authorized device location.

    Returns None if the device does not belong to the user
    or is inactive.
    """

    result = process_location_update(location)

    with SessionLocal() as db:

        device = db.scalar(
            select(Device).where(
                Device.device_id == str(location.device_id),
                Device.user_id == str(user_id),
                Device.is_active.is_(True),
            )
        )

        if device is None:
            return None

        record = DeviceLocation(
            device_id=str(location.device_id),
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy_m=location.accuracy_m,
            captured_at=location.captured_at,
            status=result.status,
        )

        db.add(record)
        db.commit()

    return result


def get_last_known_location(
    device_id: UUID,
    user_id: UUID,
) -> LocationResponse | None:
    """
    Retrieve the latest stored location belonging to this user.
    """

    with SessionLocal() as db:

        statement = (
            select(DeviceLocation)
            .join(
                Device,
                DeviceLocation.device_id == Device.device_id,
            )
            .where(
                DeviceLocation.device_id == str(device_id),
                Device.user_id == str(user_id),
                Device.is_active.is_(True),
            )
            .order_by(
                DeviceLocation.captured_at.desc(),
                DeviceLocation.received_at.desc(),
            )
            .limit(1)
        )

        record = db.scalar(statement)

        if record is None:
            return None

        message = (
            "Location received successfully."
            if record.status == "fresh"
            else "Location received, but it may be outdated."
        )

        return LocationResponse(
            device_id=UUID(record.device_id),
            latitude=record.latitude,
            longitude=record.longitude,
            accuracy_m=record.accuracy_m,
            captured_at=record.captured_at,
            status=record.status,
            message=message,
        )