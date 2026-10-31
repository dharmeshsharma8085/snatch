
from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.graph.state import SnatchState

# Core agents
from app.agents.risk_agent import (
    risk_intelligence_agent
)

from app.agents.explanation_agent import (
    openai_explanation_agent
)

from app.agents.supervisor import (
    supervisor_agent,
    route_workflow
)

# Specialist nodes
from app.graph.nodes import (
    prepare_verification,
    continue_monitoring,
    battery_guardian_node,
    location_intelligence_node,
    evidence_manager_node,
    emergency_response_node
)


# ==========================================
# SPECIALIST ROUTING
# ==========================================

def route_specialists(state: SnatchState) -> str:

    trace = state.get("agent_trace", [])
    errors = state.get("errors", [])

    # Check whether an agent has already executed
    # or returned an error.

    battery_done = (
        "Battery Guardian Agent" in trace
        or any(
            error.startswith("Battery Guardian:")
            for error in errors
        )
    )

    location_done = (
        "Location Intelligence Agent" in trace
        or any(
            error.startswith("Location Intelligence:")
            for error in errors
        )
    )

    evidence_done = (
        "Evidence Manager Agent" in trace
        or any(
            error.startswith("Evidence Manager:")
            for error in errors
        )
    )

    emergency_done = (
        "Emergency Response Agent" in trace
        or any(
            error.startswith("Emergency Response:")
            for error in errors
        )
    )

    # Execute only specialists for which
    # input data has been supplied.

    if state.get("battery_data") and not battery_done:
        return "battery"

    if state.get("location_data") and not location_done:
        return "location"

    if state.get("evidence_data") and not evidence_done:
        return "evidence"

    if state.get("emergency_data") and not emergency_done:
        return "emergency"

    return END


# ==========================================
# BUILD SNATCH GRAPH
# ==========================================

def build_snatch_graph():

    workflow = StateGraph(SnatchState)

    # --------------------------------------
    # REGISTER CORE AGENTS
    # --------------------------------------

    workflow.add_node(
        "risk_agent",
        risk_intelligence_agent
    )

    workflow.add_node(
        "explanation_agent",
        openai_explanation_agent
    )

    workflow.add_node(
        "supervisor",
        supervisor_agent
    )

    # --------------------------------------
    # REGISTER EXISTING WORKFLOW NODES
    # --------------------------------------

    workflow.add_node(
        "verification",
        prepare_verification
    )

    workflow.add_node(
        "monitoring",
        continue_monitoring
    )

    # --------------------------------------
    # REGISTER SPECIALIST AGENTS
    # --------------------------------------

    workflow.add_node(
        "battery_guardian",
        battery_guardian_node
    )

    workflow.add_node(
        "location_intelligence",
        location_intelligence_node
    )

    workflow.add_node(
        "evidence_manager",
        evidence_manager_node
    )

    workflow.add_node(
        "emergency_response",
        emergency_response_node
    )

    # --------------------------------------
    # CORE WORKFLOW
    # --------------------------------------

    workflow.add_edge(
        START,
        "risk_agent"
    )

    workflow.add_edge(
        "risk_agent",
        "explanation_agent"
    )

    workflow.add_edge(
        "explanation_agent",
        "supervisor"
    )

    # --------------------------------------
    # SUPERVISOR ROUTING
    # --------------------------------------

    workflow.add_conditional_edges(
        "supervisor",
        route_workflow,
        {
            "review": "verification",
            "monitor": "monitoring"
        }
    )

    # --------------------------------------
    # SPECIALIST ROUTING MAP
    # --------------------------------------

    specialist_routes = {
        "battery": "battery_guardian",
        "location": "location_intelligence",
        "evidence": "evidence_manager",
        "emergency": "emergency_response",
        END: END
    }

    # --------------------------------------
    # CONNECT VERIFICATION AND MONITORING
    # TO SPECIALIST ROUTER
    # --------------------------------------

    workflow.add_conditional_edges(
        "verification",
        route_specialists,
        specialist_routes
    )

    workflow.add_conditional_edges(
        "monitoring",
        route_specialists,
        specialist_routes
    )

    # --------------------------------------
    # CONNECT SPECIALIST AGENTS
    # --------------------------------------

    for node_name in [
        "battery_guardian",
        "location_intelligence",
        "evidence_manager",
        "emergency_response"
    ]:

        workflow.add_conditional_edges(
            node_name,
            route_specialists,
            specialist_routes
        )

    # --------------------------------------
    # COMPILE GRAPH
    # --------------------------------------

    return workflow.compile()


# ==========================================
# COMPILED SNATCH GRAPH
# ==========================================

snatch_graph = build_snatch_graph()
