from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.user import User
from app.models.device import Device
from app.schemas.device import DeviceCreate
from app.services import device_service


@pytest.fixture
def test_db(monkeypatch):
    # Create isolated in-memory SQLite database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create only the required tables
    User.__table__.create(engine)
    Device.__table__.create(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    # Replace production database session for this test
    monkeypatch.setattr(
        device_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    with TestingSessionLocal() as db:
        yield db

    engine.dispose()


def create_test_user(db):
    user = User(
        user_id=str(uuid4()),
        email=f"{uuid4()}@test.com",
        password_hash="test_hash",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_test_device(db, user_id, **overrides):
    values = {
        "device_id": str(uuid4()),
        "user_id": str(user_id),
        "device_name": "Test Android",
        "platform": "android",
        "is_active": True,
        "status": "offline",
        "last_seen_at": None,
    }

    values.update(overrides)

    device = Device(**values)
    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def test_device_registration(test_db):
    user = create_test_user(test_db)

    result = device_service.register_device(
        DeviceCreate(
            installation_id=uuid4(),
            device_name="Dharmesh Android",
            platform="android",
        ),
        UUID(user.user_id),
    )
    assert result.device_name == "Dharmesh Android"
    assert result.platform == "android"
    assert result.status == "offline"
    assert result.is_active is True


def test_heartbeat_marks_device_online(test_db):
    user = create_test_user(test_db)

    device = create_test_device(
        test_db,
        user.user_id,
    )

    result = device_service.update_device_heartbeat(
        UUID(device.device_id),
        UUID(user.user_id),
    )

    assert result is not None
    assert result.status == "online"
    assert result.last_seen_at is not None

    test_db.expire_all()

    updated_device = test_db.get(
        Device,
        device.device_id,
    )

    assert updated_device.status == "online"
    assert updated_device.last_seen_at is not None


def test_stale_device_marked_offline(test_db):
    user = create_test_user(test_db)

    old_heartbeat = (
        datetime.now(timezone.utc)
        - timedelta(minutes=6)
    )

    device = create_test_device(
        test_db,
        user.user_id,
        status="online",
        last_seen_at=old_heartbeat,
    )

    result = device_service.mark_stale_devices_offline(
        timeout_minutes=5
    )

    assert result == 1

    test_db.expire_all()

    updated_device = test_db.get(
        Device,
        device.device_id,
    )

    assert updated_device.status == "offline"


def test_user_cannot_access_another_users_device(test_db):
    user_a = create_test_user(test_db)
    user_b = create_test_user(test_db)

    device = create_test_device(
        test_db,
        user_a.user_id,
    )

    result = device_service.get_device(
        UUID(device.device_id),
        UUID(user_b.user_id),
    )

    assert result is None


def test_inactive_device_heartbeat_rejected(test_db):
    user = create_test_user(test_db)

    device = create_test_device(
        test_db,
        user.user_id,
        is_active=False,
    )

    result = device_service.update_device_heartbeat(
        UUID(device.device_id),
        UUID(user.user_id),
    )

    assert result is None

    test_db.expire_all()

    updated_device = test_db.get(
        Device,
        device.device_id,
    )

    assert updated_device.status == "offline"
    assert updated_device.last_seen_at is None
    
    
def test_device_deactivation(test_db):
    user = create_test_user(test_db)
    device = create_test_device(test_db, user.user_id)

    result = device_service.set_device_active_status(
        UUID(device.device_id),
        UUID(user.user_id),
        False,
    )

    assert result is not None
    assert result.is_active is False
    assert result.status == "offline"


def test_device_reactivation(test_db):
    user = create_test_user(test_db)

    device = create_test_device(
        test_db,
        user.user_id,
        is_active=False,
        status="offline",
    )

    result = device_service.set_device_active_status(
        UUID(device.device_id),
        UUID(user.user_id),
        True,
    )

    assert result is not None
    assert result.is_active is True
    assert result.status == "offline"
    
def test_duplicate_registration_same_user(test_db):
    user = create_test_user(test_db)
    installation_id = uuid4()

    data = DeviceCreate(
        installation_id=installation_id,
        device_name="Test Android",
        platform="android",
    )

    first = device_service.register_device(
        data, UUID(user.user_id)
    )

    second = device_service.register_device(
        data, UUID(user.user_id)
    )

    assert first.device_id == second.device_id


def test_duplicate_registration_different_user(test_db):
    user_a = create_test_user(test_db)
    user_b = create_test_user(test_db)

    installation_id = uuid4()

    data = DeviceCreate(
        installation_id=installation_id,
        device_name="Test Android",
        platform="android",
    )

    first = device_service.register_device(
        data, UUID(user_a.user_id)
    )

    second = device_service.register_device(
        data, UUID(user_b.user_id)
    )

    assert first is not None
    assert second is None