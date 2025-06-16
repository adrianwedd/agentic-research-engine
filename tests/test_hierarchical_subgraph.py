import asyncio

from engine.orchestration_engine import GraphState, OrchestrationEngine


def test_subgraph_node_executes_and_returns_state():
    parent = OrchestrationEngine()
    sub = OrchestrationEngine()

    def sub_start(state: GraphState) -> GraphState:
        state.update({"sub": 1})
        return state

    def sub_end(state: GraphState) -> GraphState:
        state.update({"sub_done": True})
        return state

    sub.add_node("s1", sub_start)
    sub.add_node("s2", sub_end)
    sub.add_edge("s1", "s2")

    parent.add_node("start", lambda s, sp: s)
    parent.add_subgraph("child", sub)
    parent.add_node("finish", lambda s, sp: s)
    parent.add_edge("start", "child")
    parent.add_edge("child", "finish")

    result = asyncio.run(parent.run_async(GraphState()))
    assert result.data["sub"] == 1
    assert result.data["sub_done"] is True
