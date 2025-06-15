import asyncio

import pytest

from engine.orchestration_engine import GraphState, create_orchestration_engine
from engine.routing import RoutingError, make_status_router


def test_conditional_router_executes_verifier():
    engine = create_orchestration_engine()

    def start(state: GraphState) -> GraphState:
        state.data.setdefault("order", []).append("Start")
        return state

    def verifier(state: GraphState) -> GraphState:
        state.data["order"].append("Verifier")
        state.data["status"] = "approved"
        return state

    def complete(state: GraphState) -> GraphState:
        state.data["order"].append("Complete")
        return state

    engine.add_node("Start", start)
    engine.add_node("Verifier", verifier)
    engine.add_node("Complete", complete)

    router = make_status_router(
        {
            "requires_verification": "Verifier",
            "approved": "Complete",
        }
    )

    engine.add_router("Start", router)
    engine.add_edge("Verifier", "Complete")

    state = GraphState(data={"status": "requires_verification"})

    result = asyncio.run(engine.run_async(state))

    assert result["data"]["order"] == ["Start", "Verifier", "Complete"]


def test_conditional_router_invalid_status_raises():
    engine = create_orchestration_engine()

    def start(state: GraphState) -> GraphState:
        state.data.setdefault("order", []).append("Start")
        return state

    engine.add_node("Start", start)

    router = make_status_router({"requires_verification": "Verifier"})
    engine.add_router("Start", router)

    state = GraphState(data={"status": "unknown"})

    with pytest.raises(RoutingError):
        asyncio.run(engine.run_async(state))
