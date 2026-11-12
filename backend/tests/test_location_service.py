
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.user import User
from app.models.device import Device
from app.models.location import DeviceLocation

from app.schemas.location import LocationUpdate
from app.services import location_service


@pytest.fixture
def location_db(monkeypatch):
    """Create an isolated SQLite database for location tests."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Device.__table__,
            DeviceLocation.__table__,
        ],
    )

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(
        location_service,
        "SessionLocal",
        TestSessionLocal,
    )

    user_id = uuid4()
    device_id = uuid4()

    with TestSessionLocal() as db:
        user = User(
            user_id=str(user_id),
            email="location-test@example.com",
            password_hash="test-hash",
            is_active=True,
        )

        device = Device(
            device_id=str(device_id),
            installation_id=str(uuid4()),
            user_id=str(user_id),
            device_name="Test Device",
            platform="simulator",
            is_active=True,
            status="offline",
        )

        db.add(user)
        db.add(device)
        db.commit()

    yield user_id, device_id, TestSessionLocal

    engine.dispose()

def create_location(
    device_id=None,
    consent=True,
    captured_at=None,
    latitude=28.6139,
):
    return LocationUpdate(
        device_id=device_id or uuid4(),
        latitude=latitude,
        longitude=77.2090,
        accuracy_m=10,
        captured_at=captured_at or datetime.now(timezone.utc),
        consent_granted=consent,
    )

# -------------------------------
# Validation tests
# -------------------------------

def test_fresh_location():
    location = create_location()

    result = location_service.process_location_update(location)

    assert result.status == "fresh"


def test_location_without_consent():
    location = create_location(consent=False)

    with pytest.raises(PermissionError):
        location_service.process_location_update(location)


def test_stale_location():
    old_time = datetime.now(timezone.utc) - timedelta(minutes=30)

    location = create_location(captured_at=old_time)

    result = location_service.process_location_update(location)

    assert result.status == "stale"


def test_future_timestamp():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)

    location = create_location(captured_at=future_time)

    with pytest.raises(ValueError):
        location_service.process_location_update(location)


# -------------------------------
# Database persistence tests
# -------------------------------

def test_save_and_get_last_known_location(location_db):
    user_id, device_id, _ = location_db

    location = create_location(device_id=device_id)

    saved = location_service.save_location_update(
        location,
        user_id,
    )

    assert saved is not None
    assert saved.status == "fresh"

    retrieved = location_service.get_last_known_location(
        device_id,
        user_id,
    )

    assert retrieved is not None
    assert retrieved.device_id == device_id
    assert retrieved.latitude == 28.6139
    assert retrieved.longitude == 77.2090


def test_cannot_save_another_users_device_location(location_db):
    _, device_id, _ = location_db

    another_user_id = uuid4()
    location = create_location(device_id=device_id)

    result = location_service.save_location_update(
        location,
        another_user_id,
    )

    assert result is None


def test_inactive_device_cannot_save_location(location_db):
    user_id, device_id, TestSessionLocal = location_db

    with TestSessionLocal() as db:
        device = db.get(Device, str(device_id))
        device.is_active = False
        db.commit()

    location = create_location(device_id=device_id)

    result = location_service.save_location_update(
        location,
        user_id,
    )

    assert result is None


def test_user_cannot_get_another_users_location(location_db):
    user_id, device_id, _ = location_db

    location = create_location(device_id=device_id)

    location_service.save_location_update(
        location,
        user_id,
    )

    another_user_id = uuid4()

    result = location_service.get_last_known_location(
        device_id,
        another_user_id,
    )

    assert result is None


def test_last_known_location_returns_latest_record(location_db):
    user_id, device_id, _ = location_db
    older_location = create_location(
        device_id=device_id,
        captured_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        latitude=28.5,
    )

    newer_location = create_location(
        device_id=device_id,
        captured_at=datetime.now(timezone.utc),
        latitude=28.7,
    )
    location_service.save_location_update(
        older_location,
        user_id,
    )

    location_service.save_location_update(
        newer_location,
        user_id,
    )

    result = location_service.get_last_known_location(
        device_id,
        user_id,
    )
    
    

    assert result is not None
    assert result.latitude == newer_location.latitude


def test_inactive_device_cannot_get_last_known_location(location_db):
    user_id, device_id, TestSessionLocal = location_db

    location = create_location(device_id=device_id)

    location_service.save_location_update(
        location,
        user_id,
    )

    with TestSessionLocal() as db:
        device = db.get(Device, str(device_id))
        device.is_active = False
        db.commit()

    result = location_service.get_last_known_location(
        device_id,
        user_id,
    )

    assert result is None