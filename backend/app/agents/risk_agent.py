
from app.graph.state import SnatchState
from app.services.risk_engine import calculate_risk


def risk_intelligence_agent(
    state: SnatchState
) -> dict:

    event = state["event"]

    signals = list(event.get("signals", []))

    # Include explicit user report as a signal
    if event.get("user_reported_theft"):
        signals.append("user_reported_theft")

    assessment = calculate_risk(signals)

    trace = state.get("agent_trace", [])

    trace.append("Risk Intelligence Agent")

    return {
        "risk_assessment": assessment,
        "agent_trace": trace
    }
