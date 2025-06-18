import asyncio

import pytest

from engine.orchestration_engine import GraphState, create_orchestration_engine
from engine.state import State
from services.hitl_review import InMemoryReviewQueue


def _build_engine(queue):
    engine = create_orchestration_engine()
    engine.review_queue = queue

    def node_a(state: GraphState, scratchpad: dict) -> GraphState:
        state.update({"a": 1})
        return state

    def node_b(state: GraphState, scratchpad: dict) -> GraphState:
        state.update({"b": 2})
        return state

    engine.add_node("A", node_a)
    engine.add_node("B", node_b)
    engine.add_edge("A", "B")
    return engine


def test_manual_autonomy_pauses():
    queue = InMemoryReviewQueue()
    engine = _build_engine(queue)
    state = GraphState()
    state.autonomy_level = State.AutonomyLevel.MANUAL
    result = asyncio.run(engine.run_async(state, thread_id="t1"))
    assert result.status == "PAUSED"
    assert queue.pending() == ["t1"]
    resumed = asyncio.run(engine.resume_from_queue_async("t1"))
    assert resumed.data["b"] == 2
    assert resumed.status is None


@pytest.mark.asyncio
async def test_pause_method_halts_execution():
    engine = create_orchestration_engine()

    async def node_a(state: GraphState, _):
        state.update({"count": 1})
        return state

    async def node_b(state: GraphState, _):
        await asyncio.sleep(0.05)
        state.update({"count": state.data["count"] + 1})
        return state

    engine.add_node("A", node_a)
    engine.add_node("B", node_b)
    engine.add_edge("A", "B")

    state = GraphState()
    task = asyncio.create_task(engine.run_async(state, thread_id="t"))
    await asyncio.sleep(0.02)
    engine.pause("t")
    result = await task
    assert result.status == "PAUSED"
    assert result.data["count"] == 1
