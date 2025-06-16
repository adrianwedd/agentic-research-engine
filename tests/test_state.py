import pytest

from engine.orchestration_engine import OrchestrationEngine
from engine.state import State

pytestmark = pytest.mark.core


def test_state_scratchpad_roundtrip_and_default():
    state = State()
    assert state.scratchpad == {}
    state.scratchpad["foo"] = "bar"
    payload = state.to_json()
    restored = State.from_json(payload)
    assert restored.scratchpad == {"foo": "bar"}


def test_state_serialization_roundtrip():
    state = State(data={"count": 1}, messages=[{"content": "hi"}], status="ok")
    payload = state.to_json()
    restored = State.from_json(payload)
    assert restored == state


def test_state_history_and_roundtrip():
    state = State()
    state.update({"foo": 1})
    state.add_message({"content": "bar"})
    payload = state.to_json()
    restored = State.from_json(payload)
    assert restored == state
    assert restored.history == [
        {"action": "update", "data": {"foo": 1}},
        {"action": "add_message", "message": {"content": "bar"}},
    ]


def test_state_propagates_between_nodes():
    engine = OrchestrationEngine()

    def node_a(state: State, scratchpad: dict) -> State:
        state.update({"count": state.data.get("count", 0) + 1})
        state.add_message({"content": "from_a"})
        return state

    def node_b(state: State, scratchpad: dict) -> State:
        state.update({"seen": state.data["count"]})
        return state

    engine.add_node("a", node_a)
    engine.add_node("b", node_b)
    engine.add_edge("a", "b")

    final_state = engine.run(State())
    assert final_state.data["count"] == 1
    assert final_state.data["seen"] == 1
    assert final_state.messages[-1]["content"] == "from_a"


def test_parallel_updates_preserve_history():
    engine1 = OrchestrationEngine()
    engine2 = OrchestrationEngine()

    def node_a(state: State, scratchpad: dict) -> State:
        state.update({"a": 1})
        state.add_message({"content": "A"})
        return state

    def node_b(state: State, scratchpad: dict) -> State:
        state.update({"b": 2})
        state.add_message({"content": "B"})
        return state

    engine1.add_node("a", node_a)
    engine2.add_node("b", node_b)

    import asyncio

    from engine.orchestration_engine import parallel_subgraphs

    merged = asyncio.run(parallel_subgraphs([engine1, engine2], State()))

    assert merged.data == {"a": 1, "b": 2}
    assert any(e.get("message", {}).get("content") == "A" for e in merged.history)
    assert any(e.get("message", {}).get("content") == "B" for e in merged.history)


def test_scratchpad_passthrough_when_unused():
    engine = OrchestrationEngine()

    def node_a(state: State, scratchpad: dict) -> State:
        return state

    def node_b(state: State, scratchpad: dict) -> State:
        return state

    engine.add_node("a", node_a)
    engine.add_node("b", node_b)
    engine.add_edge("a", "b")

    init = State(scratchpad={"foo": "bar"})
    final = engine.run(init)
    assert final.scratchpad == {"foo": "bar"}
