
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.graph.workflow import snatch_graph


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



def test_all_specialists_workflow():

    device_id = str(uuid4())
    incident_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

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
                str(uuid4())
            ],
            "owner_approved": True
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

    assert result["emergency_status"]["status"] == "approved_pending_delivery"

    expected_agents = [
        "Battery Guardian Agent",
        "Location Intelligence Agent",
        "Evidence Manager Agent",
        "Emergency Response Agent"
    ]

    for agent in expected_agents:
        assert agent in result["agent_trace"]

    assert result["errors"] == []
