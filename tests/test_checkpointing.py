import asyncio

from engine.orchestration_engine import (
    GraphState,
    InMemorySaver,
    create_orchestration_engine,
)


def test_resume_from_checkpoint():
    cp = InMemorySaver()
    engine = create_orchestration_engine()
    engine.checkpointer = cp

    flag = {"fail": True}

    def node_a(state: GraphState, _sp: dict) -> GraphState:
        state.update({"x": 1})
        return state

    def node_b(state: GraphState, _sp: dict) -> GraphState:
        if flag["fail"]:
            raise RuntimeError("boom")
        state.update({"x": state.data["x"] + 1})
        return state

    engine.add_node("A", node_a)
    engine.add_node("B", node_b)
    engine.add_edge("A", "B")

    try:
        asyncio.run(engine.run_async(GraphState(), thread_id="t1"))
    except RuntimeError:
        pass

    saved = cp.load("t1")
    assert saved and saved[0] == "A"

    flag["fail"] = False
    resumed = asyncio.run(engine.resume_from_checkpoint_async("t1"))
    assert resumed.data["x"] == 2
