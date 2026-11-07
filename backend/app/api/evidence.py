
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.core.security import get_current_user

from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse,
)

from app.services.evidence_service import (
    create_evidence,
    get_evidence,
    verify_evidence,
)


router = APIRouter(
    prefix="/api/v1/evidence",
    tags=["Evidence Manager"],
)


@router.post(
    "/",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_evidence(
    data: EvidenceCreate,
    current_user=Depends(get_current_user),
):
    try:
        return create_evidence(
            data,
            user_id=UUID(str(current_user.user_id)),
        )

    except PermissionError:
        raise HTTPException(
            status_code=404,
            detail="Active device not found for this user.",
        )


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
)
def read_evidence(
    evidence_id: UUID,
    current_user=Depends(get_current_user),
):
    evidence = get_evidence(
        evidence_id,
        user_id=UUID(str(current_user.user_id)),
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found.",
        )

    return evidence


@router.get("/{evidence_id}/verify")
def check_evidence(
    evidence_id: UUID,
    current_user=Depends(get_current_user),
):
    evidence = get_evidence(
        evidence_id,
        user_id=UUID(str(current_user.user_id)),
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found.",
        )

    integrity_verified = verify_evidence(
        evidence_id,
        user_id=UUID(str(current_user.user_id)),
    )

    return {
        "evidence_id": str(evidence_id),
        "integrity_verified": integrity_verified,
    }
