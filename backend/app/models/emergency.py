
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Index,
    JSON,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Emergency(Base):
    __tablename__ = "emergency_records"

    emergency_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incidents.incident_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trigger_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    trusted_contact_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    owner_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="pending_owner_approval",
    )

    delivery_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="not_started",
    )

    recipient_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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
        Index(
            "ix_emergency_user_created",
            "user_id",
            "created_at",
        ),
    )
