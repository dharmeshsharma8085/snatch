from datetime import timezone
import hashlib
import json

from uuid import UUID

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.device import Device
from app.models.evidence import Evidence

from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse,
)


def generate_evidence_hash(
    evidence: EvidenceResponse,
) -> str:

    recorded_at = evidence.recorded_at

    # Normalize timestamp to UTC
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    else:
        recorded_at = recorded_at.astimezone(timezone.utc)

    evidence_data = {
        "evidence_id": str(evidence.evidence_id),
        "device_id": str(evidence.device_id),
        "evidence_type": evidence.evidence_type,
        "source": evidence.source,
        "recorded_at": recorded_at.isoformat(),
        "payload": evidence.payload,
    }

    canonical_data = json.dumps(
        evidence_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()

def _to_response(record: Evidence) -> EvidenceResponse:

    recorded_at = record.recorded_at

    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    else:
        recorded_at = recorded_at.astimezone(timezone.utc)
    
    return EvidenceResponse(
        evidence_id=UUID(record.evidence_id),
        device_id=UUID(record.device_id),
        evidence_type=record.evidence_type,
        source=record.source,
        recorded_at=recorded_at,
        payload=record.payload,
        sha256_hash=record.sha256_hash,
        integrity_status=record.integrity_status,
    )


def create_evidence(
    data: EvidenceCreate,
    user_id: UUID | None = None,
) -> EvidenceResponse:
    """
    Create and persist evidence.

    user_id=None is reserved for internal simulated workflows.
    Authenticated API requests should provide the owner user_id.
    """

    with SessionLocal() as db:

        # Verify ownership when evidence is created through
        # an authenticated user request.
        if user_id is not None:

            device = db.scalar(
                select(Device).where(
                    Device.device_id == str(data.device_id),
                    Device.user_id == str(user_id),
                    Device.is_active.is_(True),
                )
            )

            if device is None:
                raise PermissionError(
                    "Active device not found for this user."
                )

        evidence = EvidenceResponse(
            device_id=data.device_id,
            evidence_type=data.evidence_type,
            source=data.source,
            recorded_at=data.recorded_at.astimezone(timezone.utc),
            payload=data.payload,
            sha256_hash="",
            integrity_status="pending",
        )

        evidence.sha256_hash = generate_evidence_hash(
            evidence
        )

        evidence.integrity_status = "verified_at_creation"

        record = Evidence(
            evidence_id=str(evidence.evidence_id),
            user_id=str(user_id) if user_id else None,
            device_id=str(evidence.device_id),
            evidence_type=evidence.evidence_type,
            source=evidence.source,
            recorded_at=evidence.recorded_at,
            payload=evidence.payload,
            sha256_hash=evidence.sha256_hash,
            integrity_status=evidence.integrity_status,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return _to_response(record)


def get_evidence(
    evidence_id: UUID,
    user_id: UUID | None = None,
) -> EvidenceResponse | None:
    """
    Retrieve evidence.

    If user_id is provided, retrieval is owner-scoped.
    """

    with SessionLocal() as db:

        statement = select(Evidence).where(
            Evidence.evidence_id == str(evidence_id)
        )

        if user_id is not None:
            statement = statement.where(
                Evidence.user_id == str(user_id)
            )

        record = db.scalar(statement)

        if record is None:
            return None

        return _to_response(record)


def verify_evidence(
    evidence_id: UUID,
    user_id: UUID | None = None,
) -> bool:
    """
    Recalculate SHA-256 from the persisted evidence record.
    """

    evidence = get_evidence(
        evidence_id=evidence_id,
        user_id=user_id,
    )

    if evidence is None:
        return False

    current_hash = generate_evidence_hash(evidence)

    return current_hash == evidence.sha256_hash
