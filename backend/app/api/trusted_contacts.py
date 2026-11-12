
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.trusted_contact import (
    TrustedContactCreate,
    TrustedContactUpdate,
    TrustedContactResponse,
)
from app.services.trusted_contact_service import (
    create_trusted_contact,
    get_trusted_contacts,
    update_trusted_contact,
    delete_trusted_contact,
)

router = APIRouter(
    prefix="/api/v1/contacts",
    tags=["Trusted Contacts"],
)


@router.post(
    "/",
    response_model=TrustedContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_contact(
    data: TrustedContactCreate,
    current_user=Depends(get_current_user),
):
    return create_trusted_contact(
        data=data,
        user_id=UUID(str(current_user.user_id)),
    )


@router.get(
    "/",
    response_model=list[TrustedContactResponse],
)
def list_contacts(
    current_user=Depends(get_current_user),
):
    return get_trusted_contacts(
        user_id=UUID(str(current_user.user_id)),
    )


@router.put(
    "/{contact_id}",
    response_model=TrustedContactResponse,
)
def edit_contact(
    contact_id: UUID,
    data: TrustedContactUpdate,
    current_user=Depends(get_current_user),
):
    contact = update_trusted_contact(
        contact_id=contact_id,
        user_id=UUID(str(current_user.user_id)),
        data=data,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trusted contact not found.",
        )

    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_contact(
    contact_id: UUID,
    current_user=Depends(get_current_user),
):
    deleted = delete_trusted_contact(
        contact_id=contact_id,
        user_id=UUID(str(current_user.user_id)),
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trusted contact not found.",
        )

    return None
