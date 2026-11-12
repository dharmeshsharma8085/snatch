
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from app.services import trusted_contact_service
from app.schemas.trusted_contact import TrustedContactCreate


@pytest.fixture
def setup_client(test_db, monkeypatch):
    user_id = uuid4()

    monkeypatch.setattr(
        trusted_contact_service,
        "SessionLocal",
        test_db,
    )

    app.dependency_overrides[get_current_user] = lambda: (
        SimpleNamespace(user_id=str(user_id))
    )

    client = TestClient(app)

    yield {
        "client": client,
        "user_id": user_id,
        "test_db": test_db,
    }

    app.dependency_overrides.pop(get_current_user, None)


def create_contact(user_id, name="Rahul Sharma"):
    return trusted_contact_service.create_trusted_contact(
        data=TrustedContactCreate(
            name=name,
            phone_number="+919876543210",
            email="rahul@example.com",
        ),
        user_id=user_id,
    )


def test_create_contact_success(setup_client):
    data = setup_client

    response = data["client"].post(
        "/api/v1/contacts/",
        json={
            "name": "Rahul Sharma",
            "phone_number": "+919876543210",
            "email": "rahul@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Rahul Sharma"
    assert response.json()["user_id"] == str(data["user_id"])
    assert response.json()["is_active"] is True


def test_list_contacts_success(setup_client):
    data = setup_client

    create_contact(data["user_id"])

    response = data["client"].get(
        "/api/v1/contacts/"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Rahul Sharma"


def test_list_contacts_only_returns_own_contacts(
    setup_client,
):
    data = setup_client

    other_user_id = uuid4()
    create_contact(other_user_id, "Other User")

    response = data["client"].get(
        "/api/v1/contacts/"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_update_contact_success(setup_client):
    data = setup_client

    contact = create_contact(data["user_id"])

    response = data["client"].put(
        f"/api/v1/contacts/{contact.contact_id}",
        json={
            "name": "Updated Name",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_user_cannot_update_another_users_contact(
    setup_client,
):
    data = setup_client

    other_user_id = uuid4()
    contact = create_contact(other_user_id)

    response = data["client"].put(
        f"/api/v1/contacts/{contact.contact_id}",
        json={
            "name": "Unauthorized Update",
        },
    )

    assert response.status_code == 404


def test_delete_contact_success(setup_client):
    data = setup_client

    contact = create_contact(data["user_id"])

    response = data["client"].delete(
        f"/api/v1/contacts/{contact.contact_id}"
    )

    assert response.status_code == 204

    remaining = trusted_contact_service.get_trusted_contacts(
        data["user_id"]
    )

    assert remaining == []


def test_user_cannot_delete_another_users_contact(
    setup_client,
):
    data = setup_client

    other_user_id = uuid4()
    contact = create_contact(other_user_id)

    response = data["client"].delete(
        f"/api/v1/contacts/{contact.contact_id}"
    )

    assert response.status_code == 404


def test_is_active_cannot_be_changed_by_user(
    setup_client,
):
    data = setup_client

    contact = create_contact(data["user_id"])

    response = data["client"].put(
        f"/api/v1/contacts/{contact.contact_id}",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_invalid_contact_input_rejected(setup_client):
    data = setup_client

    response = data["client"].post(
        "/api/v1/contacts/",
        json={
            "name": "R",
            "phone_number": "123",
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422


def test_contacts_api_requires_authentication(setup_client):
    data = setup_client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    response = data["client"].get(
        "/api/v1/contacts/"
    )

    assert response.status_code == 401
