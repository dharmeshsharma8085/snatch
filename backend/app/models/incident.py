from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Incident(Base):

    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    trigger_reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    signals: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="awaiting_owner_verification",
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