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


def test_nested_subgraphs_merge_state_back_to_parent():
    parent = OrchestrationEngine()
    sub1 = OrchestrationEngine()
    sub2 = OrchestrationEngine()

    def inner(state: GraphState) -> GraphState:
        state.update({"flag": True})
        state.scratchpad["order"].append("inner")
        return state

    sub2.add_node("inner", inner)

    def sub1_start(state: GraphState) -> GraphState:
        state.scratchpad["order"].append("sub1_start")
        return state

    sub1.add_node("sub1_start", sub1_start)
    sub1.add_subgraph("inner_sub", sub2)

    def sub1_end(state: GraphState) -> GraphState:
        state.scratchpad["order"].append("sub1_end")
        return state

    sub1.add_node("sub1_end", sub1_end)
    sub1.add_edge("sub1_start", "inner_sub")
    sub1.add_edge("inner_sub", "sub1_end")

    def start(state: GraphState, sp: dict) -> GraphState:
        sp["order"] = ["start"]
        return state

    def finish(state: GraphState, sp: dict) -> GraphState:
        sp["order"].append("finish")
        return state

    parent.add_node("start", start)
    parent.add_subgraph("sub", sub1)
    parent.add_node("finish", finish)
    parent.add_edge("start", "sub")
    parent.add_edge("sub", "finish")

    result = asyncio.run(parent.run_async(GraphState()))
    assert result.data["flag"] is True
    assert result.scratchpad["order"] == [
        "start",
        "sub1_start",
        "inner",
        "sub1_end",
        "finish",
    ]
