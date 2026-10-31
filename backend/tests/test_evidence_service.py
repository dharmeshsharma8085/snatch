from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.schemas.evidence import EvidenceCreate
from app.services.evidence_service import (
    create_evidence,
    get_evidence,
    verify_evidence,
    EVIDENCE_STORE
)


@pytest.fixture(autouse=True)
def clear_evidence():
    EVIDENCE_STORE.clear()


def create_sample_evidence():
    return EvidenceCreate(
        device_id=uuid4(),
        evidence_type="device_event",
        source="simulator",
        recorded_at=datetime.now(timezone.utc),
        payload={
            "event": "connectivity_loss",
            "battery": 15
        }
    )


def test_create_evidence():
    data = create_sample_evidence()

    result = create_evidence(data)

    assert result.evidence_id is not None
    assert result.integrity_status == "verified_at_creation"


def test_sha256_hash_length():
    result = create_evidence(create_sample_evidence())

    assert len(result.sha256_hash) == 64


def test_get_evidence():
    result = create_evidence(create_sample_evidence())

    retrieved = get_evidence(result.evidence_id)

    assert retrieved is not None
    assert retrieved.evidence_id == result.evidence_id


def test_verify_original_evidence():
    result = create_evidence(create_sample_evidence())

    assert verify_evidence(result.evidence_id) is True


def test_detect_evidence_tampering():
    result = create_evidence(create_sample_evidence())

    # Simulate unauthorized modification
    result.payload["battery"] = 100

    assert verify_evidence(result.evidence_id) is False