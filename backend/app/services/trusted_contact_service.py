
from uuid import UUID

from sqlalchemy import select, desc

from app.database.database import SessionLocal
from app.models.trusted_contact import TrustedContact
from app.schemas.trusted_contact import (
    TrustedContactCreate,
    TrustedContactUpdate,
)


def create_trusted_contact(
    data: TrustedContactCreate,
    user_id: UUID,
):
    with SessionLocal() as db:
        contact = TrustedContact(
            user_id=str(user_id),
            name=data.name,
            phone_number=data.phone_number,
            email=str(data.email) if data.email else None,
        )

        db.add(contact)
        db.commit()
        db.refresh(contact)

        return contact


def get_trusted_contacts(user_id: UUID):
    with SessionLocal() as db:
        statement = (
            select(TrustedContact)
            .where(TrustedContact.user_id == str(user_id))
            .order_by(desc(TrustedContact.created_at))
        )

        return list(db.scalars(statement).all())


def get_trusted_contact(
    contact_id: UUID,
    user_id: UUID,
):
    with SessionLocal() as db:
        statement = select(TrustedContact).where(
            TrustedContact.contact_id == str(contact_id),
            TrustedContact.user_id == str(user_id),
        )

        return db.scalar(statement)


def update_trusted_contact(
    contact_id: UUID,
    user_id: UUID,
    data: TrustedContactUpdate,
):
    with SessionLocal() as db:
        statement = select(TrustedContact).where(
            TrustedContact.contact_id == str(contact_id),
            TrustedContact.user_id == str(user_id),
        )

        contact = db.scalar(statement)

        if contact is None:
            return None

        updates = data.model_dump(exclude_unset=True)

        # Required fields cannot be cleared with null.
        for field in ("name", "phone_number"):
            if updates.get(field) is None:
                updates.pop(field, None)

        if "email" in updates and updates["email"] is not None:
            updates["email"] = str(updates["email"])

        for field, value in updates.items():
            setattr(contact, field, value)

        db.commit()
        db.refresh(contact)

        return contact


def delete_trusted_contact(
    contact_id: UUID,
    user_id: UUID,
) -> bool:
    with SessionLocal() as db:
        statement = select(TrustedContact).where(
            TrustedContact.contact_id == str(contact_id),
            TrustedContact.user_id == str(user_id),
        )

        contact = db.scalar(statement)

        if contact is None:
            return False

        db.delete(contact)
        db.commit()

        return True
