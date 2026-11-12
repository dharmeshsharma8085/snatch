from datetime import datetime, timezone
from uuid import uuid4

from app.graph import nodes
from app.schemas.evidence import EvidenceResponse


def test_workflow_evidence_uses_authenticated_user_id(monkeypatch):
    user_id = uuid4()
    device_id = uuid4()
    captured = {}

    def fake_create_evidence(data, user_id=None):
        captured["user_id"] = user_id

        return EvidenceResponse(
            device_id=device_id,
            evidence_type="device_event",
            source="android",
            recorded_at=datetime.now(timezone.utc),
            payload={"event": "test"},
            sha256_hash="a" * 64,
            integrity_status="verified_at_creation",
        )

    monkeypatch.setattr(nodes, "create_evidence", fake_create_evidence)

    result = nodes.evidence_manager_node({
        "event": {"user_id": str(user_id)},
        "evidence_data": {
            "device_id": str(device_id),
            "evidence_type": "device_event",
            "source": "android",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "payload": {"event": "test"},
        },
        "agent_trace": [],
        "errors": [],
    })

    assert captured["user_id"] == user_id
    assert len(result["evidence_records"]) == 1
    assert "Evidence Manager Agent" in result["agent_trace"]