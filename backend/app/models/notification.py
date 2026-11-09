from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    delivery_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    emergency_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("emergency_records.emergency_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("trusted_contacts.contact_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="sms",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="queued",
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    provider_message_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    provider_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "emergency_id",
            "contact_id",
            "channel",
            name="uq_emergency_contact_channel",
        ),
        Index(
            "ix_notification_status_next_attempt",
            "status",
            "next_attempt_at",
        ),
    )