
from uuid import UUID, uuid4

from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from app.database.database import SessionLocal
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceResponse
from datetime import datetime, timezone, timedelta

from app.schemas.device import DeviceHeartbeatResponse



def to_response(device: Device) -> DeviceResponse:
    return DeviceResponse(
        device_id=UUID(device.device_id),
        user_id=UUID(device.user_id),
        device_name=device.device_name,
        platform=device.platform,
        is_active=device.is_active,
        status=device.status,
        last_seen_at=device.last_seen_at,
        created_at=device.created_at,
    )

def register_device(
    data: DeviceCreate,
    user_id: UUID,
) -> DeviceResponse | None:

    with SessionLocal() as db:

        installation_id = str(data.installation_id)

        statement = select(Device).where(
            Device.installation_id == installation_id
        )

        existing_device = db.scalar(statement)

        if existing_device is not None:
            if existing_device.user_id != str(user_id):
                return None

            return to_response(existing_device)

        device = Device(
            device_id=str(uuid4()),
            installation_id=installation_id,
            user_id=str(user_id),
            device_name=data.device_name,
            platform=data.platform,
            is_active=True,
            status="offline",
        )

        try:
            db.add(device)
            db.commit()
            db.refresh(device)

            return to_response(device)

        except IntegrityError:
            db.rollback()

            # Another request may have registered this installation.
            existing_device = db.scalar(
                select(Device).where(
                    Device.installation_id == installation_id
                )
            )

            if existing_device is not None:
                if existing_device.user_id == str(user_id):
                    return to_response(existing_device)

            return None


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
        device.status = "online"

        db.commit()
        db.refresh(device)

        return DeviceHeartbeatResponse(
            device_id=UUID(device.device_id),
            status="online",
            last_seen_at=now,
            message="Device heartbeat received successfully",
        )




def mark_stale_devices_offline(
    timeout_minutes: int = 5,
) -> int:
    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=timeout_minutes
    )

    with SessionLocal() as db:
        statement = select(Device).where(
            Device.is_active.is_(True),
            Device.status == "online",
            or_(
                Device.last_seen_at.is_(None),
                Device.last_seen_at < cutoff_time,
            ),
        )

        stale_devices = db.scalars(statement).all()

        for device in stale_devices:
            device.status = "offline"

        if stale_devices:
            db.commit()

        return len(stale_devices)

def set_device_active_status(
    device_id: UUID,
    user_id: UUID,
    is_active: bool,
) -> DeviceResponse | None:

    with SessionLocal() as db:
        statement = select(Device).where(
            Device.device_id == str(device_id),
            Device.user_id == str(user_id),
        )

        device = db.scalar(statement)

        if device is None:
            return None

        device.is_active = is_active

        # Reactivated devices must send a fresh heartbeat.
        device.status = "offline"

        db.commit()
        db.refresh(device)

        return to_response(device)