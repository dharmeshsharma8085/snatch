
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceResponse
from datetime import datetime, timezone, timedelta

from app.schemas.device import DeviceHeartbeatResponse


def to_response(device: Device) -> DeviceResponse:
    last_seen = device.last_seen_at

    if last_seen is None:
        device_status = "offline"
    else:
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        device_status = (
            "online"
            if now - last_seen <= timedelta(minutes=5)
            else "offline"
        )

    return DeviceResponse(
        device_id=UUID(device.device_id),
        user_id=UUID(device.user_id),
        device_name=device.device_name,
        platform=device.platform,
        is_active=device.is_active,
        status=device_status,
        last_seen_at=device.last_seen_at,
        created_at=device.created_at,
    )


def register_device(
    data: DeviceCreate,
    user_id: UUID,
) -> DeviceResponse:

    with SessionLocal() as db:
        device = Device(
            device_id=str(uuid4()),
            user_id=str(user_id),
            device_name=data.device_name,
            platform=data.platform,
            is_active=True,
        )

        db.add(device)
        db.commit()
        db.refresh(device)

        return to_response(device)


def get_user_devices(user_id: UUID) -> list[DeviceResponse]:

    with SessionLocal() as db:
        statement = select(Device).where(
            Device.user_id == str(user_id),
            Device.is_active.is_(True),
        )

        devices = db.scalars(statement).all()

        return [to_response(device) for device in devices]


def get_device(
    device_id: UUID,
    user_id: UUID,
) -> DeviceResponse | None:

    with SessionLocal() as db:
        statement = select(Device).where(
            Device.device_id == str(device_id),
            Device.user_id == str(user_id),
        )

        device = db.scalar(statement)

        if device is None:
            return None

        return to_response(device)



def update_device_heartbeat(
    device_id: UUID,
    user_id: UUID,
) -> DeviceHeartbeatResponse | None:

    with SessionLocal() as db:
        statement = select(Device).where(
            Device.device_id == str(device_id),
            Device.user_id == str(user_id),
            Device.is_active.is_(True),
        )

        device = db.scalar(statement)

        if device is None:
            return None

        now = datetime.now(timezone.utc)

        device.last_seen_at = now

        db.commit()
        db.refresh(device)

        return DeviceHeartbeatResponse(
            device_id=UUID(device.device_id),
            status="online",
            last_seen_at=device.last_seen_at,
            message="Device heartbeat received successfully",
        )
