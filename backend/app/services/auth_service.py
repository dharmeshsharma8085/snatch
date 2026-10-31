
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.database import SessionLocal
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse,
)

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must contain at least 32 characters"
    )

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "exp": expires_at,
        "iat": now,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def register_user(data: UserRegister) -> UserResponse:
    email = str(data.email).strip().lower()

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            raise ValueError("Email is already registered")

        user = User(
            email=email,
            password_hash=hash_password(data.password),
            is_active=True,
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)

            return UserResponse(
                user_id=user.user_id,
                email=user.email,
                is_active=user.is_active,
            )

        except IntegrityError:
            db.rollback()
            raise ValueError("Email is already registered")


def login_user(data: UserLogin) -> TokenResponse:
    email = str(data.email).strip().lower()

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if not user or not verify_password(
            data.password, user.password_hash
        ):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is inactive")

        token = create_access_token(user.user_id)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
