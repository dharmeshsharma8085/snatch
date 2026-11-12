
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from app.models.device import Device
from app.database.database import SessionLocal
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentResponse


def to_response(incident: Incident) -> IncidentResponse:
    return IncidentResponse(
        incident_id=UUID(incident.incident_id),
        user_id=UUID(incident.user_id),
        device_id=UUID(incident.device_id),
        risk_score=incident.risk_score,
        risk_level=incident.risk_level,
        trigger_reason=incident.trigger_reason,
        signals=incident.signals,
        status=incident.status,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


def create_incident(
    data: IncidentCreate,
    user_id: UUID,
) -> IncidentResponse:

    with SessionLocal() as db:

        device = db.scalar(
            select(Device).where(
                Device.device_id == str(data.device_id),
                Device.user_id == str(user_id),
                Device.is_active.is_(True),
            )
        )

        if device is None:
            raise PermissionError(
                "Active device not found for this user."
            )

        incident = Incident(
            user_id=str(user_id),
            device_id=str(data.device_id),
            risk_score=data.risk_score,
            risk_level=data.risk_level,
            trigger_reason=data.trigger_reason,
            signals=data.signals,
            status="awaiting_owner_verification",
        )

        try:
            db.add(incident)
            db.commit()
            db.refresh(incident)

            return to_response(incident)

        except Exception:
            db.rollback()
            raise

  

def get_incident(
    incident_id: UUID,
    user_id: UUID,
) -> IncidentResponse | None:

    with SessionLocal() as db:
        statement = select(Incident).where(
            Incident.incident_id == str(incident_id),
            Incident.user_id == str(user_id),
        )

        incident = db.scalar(statement)

        if incident is None:
            return None

        return to_response(incident)


def verify_incident(
    incident_id: UUID,
    user_id: UUID,
    owner_confirmed: bool,
) -> IncidentResponse | None:

    with SessionLocal() as db:
        statement = select(Incident).where(
            Incident.incident_id == str(incident_id),
            Incident.user_id == str(user_id),
        )

        incident = db.scalar(statement)

        if incident is None:
            return None

        if incident.status == "awaiting_owner_verification":
            incident.status = (
                "confirmed" if owner_confirmed else "cancelled"
            )
            incident.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(incident)

        return to_response(incident)


def cancel_incident(
    incident_id: UUID,
    user_id: UUID,
) -> IncidentResponse | None:

    with SessionLocal() as db:
        statement = select(Incident).where(
            Incident.incident_id == str(incident_id),
            Incident.user_id == str(user_id),
        )

        incident = db.scalar(statement)

        if incident is None:
            return None

        if incident.status == "awaiting_owner_verification":
            incident.status = "cancelled"
            incident.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(incident)

        return to_response(incident)
