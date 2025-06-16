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


def test_subgraph_propagates_state_and_parent_resumes():
    parent = OrchestrationEngine()
    sub = OrchestrationEngine()

    def node_a(state: GraphState, sp: dict) -> GraphState:
        sp["steps"] = ["A"]
        return state

    def sub_step(state: GraphState) -> GraphState:
        child = GraphState(**state.model_dump())
        child.scratchpad["steps"].append("SUB")
        child.scratchpad["finding"] = "value"
        return child

    def node_b(state: GraphState, sp: dict) -> GraphState:
        sp["steps"].append("B")
        return state

    sub.add_node("s1", sub_step)

    parent.add_node("start", node_a)
    parent.add_subgraph("child", sub)
    parent.add_node("end", node_b)
    parent.add_edge("start", "child")
    parent.add_edge("child", "end")

    result = asyncio.run(parent.run_async(GraphState()))
    assert result.scratchpad["finding"] == "value"
    assert result.scratchpad["steps"] == ["A", "SUB", "B"]
