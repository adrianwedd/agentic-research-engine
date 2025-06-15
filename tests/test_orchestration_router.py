import asyncio

from engine.orchestration_engine import GraphState, create_orchestration_engine


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

    def router(state: GraphState) -> str:
        return (
            "Verifier"
            if state.data.get("status") == "requires_verification"
            else "Complete"
        )

    engine.add_router("Start", router)
    engine.add_edge("Verifier", "Complete")

    state = GraphState(data={"status": "requires_verification"})

    result = asyncio.run(engine.run_async(state))

    assert result["data"]["order"] == ["Start", "Verifier", "Complete"]
