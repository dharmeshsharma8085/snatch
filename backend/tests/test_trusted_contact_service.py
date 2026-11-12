
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services import trusted_contact_service
from app.schemas.trusted_contact import (
    TrustedContactCreate,
    TrustedContactUpdate,
)


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()
    db.__enter__.return_value = db
    db.__exit__.return_value = False

    monkeypatch.setattr(
        trusted_contact_service,
        "SessionLocal",
        lambda: db,
    )
    return db


@pytest.fixture
def ids():
    return {
        "user_id": uuid4(),
        "contact_id": uuid4(),
    }


@pytest.fixture
def contact_data():
    return TrustedContactCreate(
        name="Rahul Sharma",
        phone_number="+919876543210",
        email="rahul@example.com",
    )


def test_create_trusted_contact_success(
    mock_db, ids, contact_data
):
    result = trusted_contact_service.create_trusted_contact(
        data=contact_data,
        user_id=ids["user_id"],
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    saved = mock_db.add.call_args.args[0]

    assert saved.user_id == str(ids["user_id"])
    assert saved.name == "Rahul Sharma"
    assert saved.phone_number == "+919876543210"
    assert saved.email == "rahul@example.com"
    assert saved.is_active is True
    assert result == saved


def test_create_trusted_contact_without_email(
    mock_db, ids
):
    data = TrustedContactCreate(
        name="Rahul Sharma",
        phone_number="+919876543210",
    )

    result = trusted_contact_service.create_trusted_contact(
        data=data,
        user_id=ids["user_id"],
    )

    assert result.email is None
    mock_db.commit.assert_called_once()


def test_get_trusted_contacts_success(mock_db, ids):
    contacts = [
        SimpleNamespace(name="Rahul"),
        SimpleNamespace(name="Amit"),
    ]

    mock_db.scalars.return_value.all.return_value = contacts

    result = trusted_contact_service.get_trusted_contacts(
        user_id=ids["user_id"],
    )

    assert result == contacts
    mock_db.scalars.assert_called_once()


def test_get_trusted_contacts_empty(mock_db, ids):
    mock_db.scalars.return_value.all.return_value = []

    result = trusted_contact_service.get_trusted_contacts(
        user_id=ids["user_id"],
    )

    assert result == []


def test_get_trusted_contact_success(mock_db, ids):
    contact = SimpleNamespace(
        contact_id=str(ids["contact_id"]),
        user_id=str(ids["user_id"]),
    )
    mock_db.scalar.return_value = contact

    result = trusted_contact_service.get_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
    )

    assert result == contact


def test_get_trusted_contact_not_found(mock_db, ids):
    mock_db.scalar.return_value = None

    result = trusted_contact_service.get_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
    )

    assert result is None


def test_update_trusted_contact_success(mock_db, ids):
    contact = SimpleNamespace(
        name="Old Name",
        phone_number="+919876543210",
        email=None,
        is_active=True,
    )
    mock_db.scalar.return_value = contact

    data = TrustedContactUpdate(
        name="New Name",
        email="new@example.com",
    )

    result = trusted_contact_service.update_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
        data=data,
    )

    assert result == contact
    assert contact.name == "New Name"
    assert contact.email == "new@example.com"
    assert contact.is_active is True

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_update_trusted_contact_not_found(mock_db, ids):
    mock_db.scalar.return_value = None

    result = trusted_contact_service.update_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
        data=TrustedContactUpdate(name="New Name"),
    )

    assert result is None
    mock_db.commit.assert_not_called()


def test_update_does_not_clear_required_fields(
    mock_db, ids
):
    contact = SimpleNamespace(
        name="Rahul",
        phone_number="+919876543210",
        email="rahul@example.com",
        is_active=True,
    )
    mock_db.scalar.return_value = contact

    data = TrustedContactUpdate(
        name=None,
        phone_number=None,
    )

    result = trusted_contact_service.update_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
        data=data,
    )

    assert result.name == "Rahul"
    assert result.phone_number == "+919876543210"
    mock_db.commit.assert_called_once()


def test_delete_trusted_contact_success(mock_db, ids):
    contact = SimpleNamespace(
        contact_id=str(ids["contact_id"]),
        user_id=str(ids["user_id"]),
    )
    mock_db.scalar.return_value = contact

    result = trusted_contact_service.delete_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
    )

    assert result is True
    mock_db.delete.assert_called_once_with(contact)
    mock_db.commit.assert_called_once()


def test_delete_trusted_contact_not_found(mock_db, ids):
    mock_db.scalar.return_value = None

    result = trusted_contact_service.delete_trusted_contact(
        contact_id=ids["contact_id"],
        user_id=ids["user_id"],
    )

    assert result is False
    mock_db.delete.assert_not_called()
    mock_db.commit.assert_not_called()
