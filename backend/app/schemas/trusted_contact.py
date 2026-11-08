
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class TrustedContactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(min_length=7, max_length=20)
    email: EmailStr | None = None


class TrustedContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone_number: str | None = Field(default=None, min_length=7, max_length=20)
    email: EmailStr | None = None
    is_active: bool | None = None


class TrustedContactResponse(BaseModel):
    contact_id: UUID
    user_id: UUID
    name: str
    phone_number: str
    email: EmailStr | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
