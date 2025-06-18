import asyncio

import pytest

from engine.orchestration_engine import (
    GraphState,
    Node,
    NodeType,
    create_orchestration_engine,
)

pytestmark = pytest.mark.core


def test_high_risk_routes_to_quarantine():
    calls = []

    def start(state: GraphState, _):
        return state

    def privileged(state: GraphState, _):
        calls.append("privileged")
        return state

    def quarantine(state: GraphState, _):
        calls.append("quarantine")
        return state

    def complete(state: GraphState, _):
        calls.append("complete")
        return state

    engine = create_orchestration_engine()
    engine.add_node("Start", start)
    engine.add_node("Quarantine", quarantine, node_type=NodeType.QUARANTINED)
    engine.add_node("Privileged", privileged, node_type=NodeType.PRIVILEGED)
    engine.add_node("Complete", complete)
    engine.add_edge("Start", "Privileged")
    engine.add_edge("Privileged", "Complete")
    engine.add_edge("Quarantine", "Complete")
    engine.set_quarantine_node("Quarantine")

    state = GraphState(data={"risk_level": "high"})
    result = asyncio.run(engine.run_async(state))
    assert result == state
    assert calls == ["quarantine", "complete"]


def test_low_risk_allows_privileged():
    calls = []

    def start(state: GraphState, _):
        return state

    def privileged(state: GraphState, _):
        calls.append("privileged")
        return state

    def quarantine(state: GraphState, _):
        calls.append("quarantine")
        return state

    def complete(state: GraphState, _):
        calls.append("complete")
        return state

    engine = create_orchestration_engine()
    engine.add_node("Start", start)
    engine.add_node("Quarantine", quarantine, node_type=NodeType.QUARANTINED)
    engine.add_node("Privileged", privileged, node_type=NodeType.PRIVILEGED)
    engine.add_node("Complete", complete)
    engine.add_edge("Start", "Privileged")
    engine.add_edge("Privileged", "Complete")
    engine.add_edge("Quarantine", "Complete")
    engine.set_quarantine_node("Quarantine")

    state = GraphState(data={"risk_level": "low"})
    asyncio.run(engine.run_async(state))
    assert calls == ["privileged", "complete"]


def test_privileged_node_rejects_high_risk():
    node = Node("P", lambda s, _: s, node_type=NodeType.PRIVILEGED)
    state = GraphState(data={"risk_level": "high"})
    with pytest.raises(PermissionError):
        asyncio.run(node.run(state))
