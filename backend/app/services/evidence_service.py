import hashlib
import json

from uuid import UUID

from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse
)


# Temporary in-memory evidence storage
EVIDENCE_STORE: dict[UUID, EvidenceResponse] = {}


def generate_evidence_hash(
    evidence: EvidenceResponse
) -> str:

    # Create a deterministic representation
    evidence_data = {
        "evidence_id": str(evidence.evidence_id),
        "device_id": str(evidence.device_id),
        "evidence_type": evidence.evidence_type,
        "source": evidence.source,
        "recorded_at": evidence.recorded_at.isoformat(),
        "payload": evidence.payload
    }

    canonical_data = json.dumps(
        evidence_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


def create_evidence(
    data: EvidenceCreate
) -> EvidenceResponse:

    # Create initial evidence record
    evidence = EvidenceResponse(
        device_id=data.device_id,
        evidence_type=data.evidence_type,
        source=data.source,
        recorded_at=data.recorded_at,
        payload=data.payload,
        sha256_hash="",
        integrity_status="pending"
    )

    # Generate SHA-256 hash
    evidence.sha256_hash = generate_evidence_hash(
        evidence
    )

    evidence.integrity_status = "verified_at_creation"

    # Store evidence
    EVIDENCE_STORE[evidence.evidence_id] = evidence

    return evidence


def get_evidence(
    evidence_id: UUID
) -> EvidenceResponse | None:

    return EVIDENCE_STORE.get(evidence_id)


def verify_evidence(
    evidence_id: UUID
) -> bool:

    evidence = get_evidence(evidence_id)

    if evidence is None:
        return False

    current_hash = generate_evidence_hash(evidence)

    return current_hash == evidence.sha256_hash