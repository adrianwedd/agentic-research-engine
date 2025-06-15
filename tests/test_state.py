from engine.orchestration_engine import OrchestrationEngine
from engine.state import State


def test_state_serialization_roundtrip():
    state = State(data={"count": 1}, messages=[{"content": "hi"}], status="ok")
    payload = state.to_json()
    restored = State.from_json(payload)
    assert restored == state


def test_state_propagates_between_nodes():
    engine = OrchestrationEngine()

    def node_a(state: State) -> State:
        state.update({"count": state.data.get("count", 0) + 1})
        state.add_message({"content": "from_a"})
        return state

    def node_b(state: State) -> State:
        state.update({"seen": state.data["count"]})
        return state

    engine.add_node("a", node_a)
    engine.add_node("b", node_b)
    engine.add_edge("a", "b")

    final_state = engine.run(State())
    assert final_state.data["count"] == 1
    assert final_state.data["seen"] == 1
    assert final_state.messages[-1]["content"] == "from_a"
