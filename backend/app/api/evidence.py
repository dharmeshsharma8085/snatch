from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse
)

from app.services.evidence_service import (
    create_evidence,
    get_evidence,
    verify_evidence
)


router = APIRouter(
    prefix="/api/v1/evidence",
    tags=["Evidence Manager"]
)


@router.post("/", response_model=EvidenceResponse)
def add_evidence(data: EvidenceCreate):

    return create_evidence(data)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def read_evidence(evidence_id: UUID):

    evidence = get_evidence(evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    return evidence


@router.get("/{evidence_id}/verify")
def check_evidence(evidence_id: UUID):

    evidence = get_evidence(evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    return {
        "evidence_id": str(evidence_id),
        "integrity_verified": verify_evidence(evidence_id)
    }