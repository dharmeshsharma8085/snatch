
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.graph.workflow import snatch_graph
from app.models.user import User
from app.models.device import Device
from app.models.incident import Incident
from app.models.trusted_contact import TrustedContact
from app.services import emergency_service

def test_multi_agent_battery_workflow():

    device_id = str(uuid4())

    initial_state = {
        "event": {
            "event_id": str(uuid4()),
            "user_id": str(uuid4()),
            "device_id": device_id,
            "platform": "simulator",
            "event_type": "suspicious_activity",
            "signals": [
                "unusual_motion",
                "connectivity_loss",
                "charger_disconnected"
            ],
            "occurred_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "user_reported_theft": False
        },

        "battery_data": {
            "device_id": device_id,
            "battery_level": 10,
            "is_charging": False,
            "captured_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "platform": "simulator"
        },

        "agent_trace": [],
        "errors": []
    }

    result = asyncio.run(
        snatch_graph.ainvoke(initial_state)
    )

    assert "risk_assessment" in result

    assert "battery_assessment" in result

    assert (
        result["battery_assessment"]["battery_status"]
        == "critical"
    )

    assert (
        "Battery Guardian Agent"
        in result["agent_trace"]
    )


def test_all_specialists_workflow(test_db, monkeypatch):
    device_id = str(uuid4())
    incident_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    user_id = str(uuid4())
    contact_id = str(uuid4())

    monkeypatch.setattr(
        emergency_service,
        "SessionLocal",
        test_db
    )

    with test_db() as db:
        user = User(
            user_id=user_id,
            email=f"{user_id}@test.com",
            password_hash="test-hash",
            is_active=True,
        )

        device = Device(
            device_id=device_id,
            user_id=user_id,
            device_name="Workflow Test Device",
            platform="android",
            is_active=True,
        )

        incident = Incident(
            incident_id=incident_id,
            user_id=user_id,
            device_id=device_id,
            risk_score=95,
            risk_level="critical",
            trigger_reason="Simulated suspicious activity",
            signals=[
                "unusual_motion",
                "connectivity_loss",
                "charger_disconnected",
                "location_anomaly",
                "user_reported_theft",
            ],
            status="awaiting_owner_verification",
        )

        contact = TrustedContact(
            contact_id=contact_id,
            user_id=user_id,
            name="Test Contact",
            phone_number="+919876543210",
            is_active=True,
        )

        db.add_all([user, device, incident, contact])
        db.commit()

    initial_state = {
        "event": {
            "event_id": str(uuid4()),
            "user_id": user_id,
            "device_id": device_id,
            "platform": "simulator",
            "event_type": "suspicious_activity",
            "signals": [
                "unusual_motion",
                "connectivity_loss",
                "charger_disconnected",
                "location_anomaly",
                "user_reported_theft"
            ],
            "occurred_at": now,
            "user_reported_theft": True
        },

        "battery_data": {
            "device_id": device_id,
            "battery_level": 10,
            "is_charging": False,
            "captured_at": now,
            "platform": "simulator"
        },

        "location_data": {
            "device_id": device_id,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "accuracy_m": 10,
            "captured_at": now,
            "consent_granted": True
        },

        "evidence_data": {
            "device_id": device_id,
            "evidence_type": "device_event",
            "source": "simulator",
            "recorded_at": now,
            "payload": {
                "event": "simulated_suspicious_activity"
            }
        },

        "emergency_data": {
            "incident_id": incident_id,
            "device_id": device_id,
            "trigger_reason": "Simulated emergency test",
            "trusted_contact_ids": [
                contact_id
            ],

        },

        "incident_id": incident_id,
        "agent_trace": [],
        "errors": []
    }

    result = asyncio.run(
        snatch_graph.ainvoke(initial_state)
    )

    assert result["risk_assessment"]["score"] == 95

    assert result["battery_assessment"]["battery_status"] == "critical"

    assert result["location_assessment"]["status"] == "fresh"

    assert len(result["evidence_records"]) == 1

    assert result["emergency_status"]["status"] == "pending_owner_approval"
    assert result["emergency_status"]["owner_approved"] is False
    expected_agents = [
        "Battery Guardian Agent",
        "Location Intelligence Agent",
        "Evidence Manager Agent",
        "Emergency Response Agent"
    ]

    for agent in expected_agents:
        assert agent in result["agent_trace"]

    assert result["errors"] == []
