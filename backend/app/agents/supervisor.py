from app.graph.state import SnatchState


def route_workflow(state: SnatchState) -> str:
    assessment = state["risk_assessment"]
    score = assessment["score"]

    if score >= 50:
        return "review"

    return "monitor"


def supervisor_agent(state: SnatchState) -> dict:

    trace = list(state.get("agent_trace", []))
    trace.append("SNATCH Supervisor")

    route = route_workflow(state)

    if route == "review":
        action = "provisional_incident_and_owner_verification"
    else:
        action = "record_and_monitor"

    return {
        "next_action": action,
        "agent_trace": trace
    }