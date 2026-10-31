
from typing import Any


SIGNAL_WEIGHTS = {
    "unusual_motion": 20,
    "connectivity_loss": 15,
    "charger_disconnected": 10,
    "location_anomaly": 15,
    "critical_battery": 5,
    "user_reported_theft": 35,
}


def calculate_risk(
    signals: list[str]
) -> dict[str, Any]:

    # Remove duplicate signals
    unique_signals = list(set(signals))

    # Calculate experimental risk score
    score = sum(
        SIGNAL_WEIGHTS.get(signal, 0)
        for signal in unique_signals
    )

    score = min(score, 100)

    # Determine risk category
    if score < 30:
        level = "normal"
    elif score < 50:
        level = "low"
    elif score < 70:
        level = "suspicious"
    elif score < 90:
        level = "high"
    else:
        level = "critical"

    # Determine confidence from available signals.
    if len(unique_signals) >= 3:
        confidence = "high"
    elif len(unique_signals) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # Determine recommended action
    if level == "normal":
        action = "continue_monitoring"

    elif level == "low":
        action = "record_and_monitor"

    elif level == "suspicious":
        action = "request_owner_verification"

    elif level == "high":
        action = "prioritize_owner_verification"

    else:
        action = "urgent_owner_verification"

    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "signals": unique_signals,
        "explanation": (
            "Risk calculated using available device signals."
        ),
        "recommended_action": action
    }
