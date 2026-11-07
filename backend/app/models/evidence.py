
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base
from sqlalchemy.ext.mutable import MutableDict

class Evidence(Base):
    __tablename__ = "evidence_records"

    evidence_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Nullable for simulated LangGraph evidence.
    # API-created evidence will have an authenticated owner.
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
    )

    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    integrity_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_evidence_device_recorded",
            "device_id",
            "recorded_at",
        ),
    )
