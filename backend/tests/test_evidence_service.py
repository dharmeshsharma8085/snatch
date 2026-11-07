
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.user import User
from app.models.device import Device
from app.models.evidence import Evidence

from app.schemas.evidence import EvidenceCreate
from app.services import evidence_service


@pytest.fixture
def evidence_db(monkeypatch):

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
            Evidence.__table__,
        ],
    )

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(
        evidence_service,
        "SessionLocal",
        TestSessionLocal,
    )

    user_id = uuid4()
    device_id = uuid4()

    with TestSessionLocal() as db:
        db.add(
            User(
                user_id=str(user_id),
                email="evidence-test@example.com",
                password_hash="test-hash",
                is_active=True,
            )
        )

        db.add(
            Device(
                device_id=str(device_id),
                installation_id=str(uuid4()),
                user_id=str(user_id),
                device_name="Evidence Test Device",
                platform="simulator",
                is_active=True,
                status="offline",
            )
        )

        db.commit()

    yield user_id, device_id, TestSessionLocal

    engine.dispose()


def create_sample_evidence(device_id=None):

    return EvidenceCreate(
        device_id=device_id or uuid4(),
        evidence_type="device_event",
        source="simulator",
        recorded_at=datetime.now(timezone.utc),
        payload={
            "event": "connectivity_loss",
            "battery": 15,
        },
    )


def test_create_evidence(evidence_db):

    result = evidence_service.create_evidence(
        create_sample_evidence()
    )

    assert result.evidence_id is not None
    assert result.integrity_status == "verified_at_creation"


def test_sha256_hash_length(evidence_db):

    result = evidence_service.create_evidence(
        create_sample_evidence()
    )

    assert len(result.sha256_hash) == 64


def test_get_evidence(evidence_db):

    result = evidence_service.create_evidence(
        create_sample_evidence()
    )

    retrieved = evidence_service.get_evidence(
        result.evidence_id
    )

    assert retrieved is not None
    assert retrieved.evidence_id == result.evidence_id


def test_verify_original_evidence(evidence_db):

    result = evidence_service.create_evidence(
        create_sample_evidence()
    )

    assert evidence_service.verify_evidence(
        result.evidence_id
    ) is True


def test_detect_evidence_tampering(evidence_db):

    _, _, TestSessionLocal = evidence_db

    result = evidence_service.create_evidence(
        create_sample_evidence()
    )

    # Modify the actual database record.
    with TestSessionLocal() as db:
        record = db.get(
            Evidence,
            str(result.evidence_id),
        )

        record.payload["battery"] = 100
        db.commit()

    assert evidence_service.verify_evidence(
        result.evidence_id
    ) is False


def test_evidence_persists_in_database(evidence_db):

    _, _, TestSessionLocal = evidence_db

    result = evidence_service.create_evidence(
        create_sample_evidence()
    )

    # Retrieve using a separate database session.
    with TestSessionLocal() as db:
        record = db.get(
            Evidence,
            str(result.evidence_id),
        )

        assert record is not None
        assert record.sha256_hash == result.sha256_hash


def test_evidence_owner_validation(evidence_db):

    user_id, device_id, _ = evidence_db

    result = evidence_service.create_evidence(
        create_sample_evidence(device_id),
        user_id=user_id,
    )

    assert result is not None

    retrieved = evidence_service.get_evidence(
        result.evidence_id,
        user_id=user_id,
    )

    assert retrieved is not None


def test_another_user_cannot_access_evidence(evidence_db):

    user_id, device_id, _ = evidence_db

    result = evidence_service.create_evidence(
        create_sample_evidence(device_id),
        user_id=user_id,
    )

    another_user_id = uuid4()

    retrieved = evidence_service.get_evidence(
        result.evidence_id,
        user_id=another_user_id,
    )

    assert retrieved is None


def test_another_user_cannot_register_evidence(evidence_db):

    _, device_id, _ = evidence_db

    another_user_id = uuid4()

    with pytest.raises(PermissionError):
        evidence_service.create_evidence(
            create_sample_evidence(device_id),
            user_id=another_user_id,
        )
