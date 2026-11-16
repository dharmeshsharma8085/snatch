
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class WebhookNonce(Base):
    __tablename__ = "webhook_nonces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    nonce: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_webhook_nonce_expiry", "expires_at"),
    )
