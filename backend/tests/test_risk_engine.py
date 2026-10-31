from app.services.risk_engine import calculate_risk


def test_normal_risk():
    result = calculate_risk([])
    assert result["score"] == 0
    assert result["level"] == "normal"


def test_low_risk():
    result = calculate_risk([
        "unusual_motion",
        "connectivity_loss",
        "charger_disconnected"
    ])
    assert result["score"] == 45
    assert result["level"] == "low"


def test_critical_risk():
    result = calculate_risk([
        "unusual_motion",
        "connectivity_loss",
        "charger_disconnected",
        "location_anomaly",
        "user_reported_theft"
    ])
    assert result["score"] == 95
    assert result["level"] == "critical"


def test_duplicate_signals():
    result = calculate_risk([
        "unusual_motion",
        "unusual_motion"
    ])
    assert result["score"] == 20
    assert len(result["signals"]) == 1


def test_unknown_signal():
    result = calculate_risk(["unknown_signal"])
    assert result["score"] == 0
    assert result["level"] == "normal"