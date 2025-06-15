import asyncio
from threading import Thread

import requests

from engine.orchestration_engine import (
    GraphState,
    NodeType,
    create_orchestration_engine,
)
from services.hitl_review import HITLReviewServer, InMemoryReviewQueue


def _build_engine(queue: InMemoryReviewQueue):
    engine = create_orchestration_engine()
    engine.review_queue = queue

    def node_a(state: GraphState) -> GraphState:
        state.update({"a": 1})
        return state

    def node_b(state: GraphState) -> GraphState:
        state.update({"b": 2})
        return state

    engine.add_node("A", node_a)
    engine.add_node(
        "Break",
        lambda s: s,
        node_type=NodeType.HUMAN_IN_THE_LOOP_BREAKPOINT,
    )
    engine.add_node("B", node_b)
    engine.add_edge("A", "Break")
    engine.add_edge("Break", "B")
    return engine


def _start_server(engine, queue):
    server = HITLReviewServer(queue, engine, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.httpd.server_port}"


def test_breakpoint_pauses_and_resumes():
    queue = InMemoryReviewQueue()
    engine = _build_engine(queue)
    state = asyncio.run(engine.run_async(GraphState(), thread_id="t1"))
    assert state.status == "PAUSED"
    assert queue.pending() == ["t1"]

    resumed = asyncio.run(engine.resume_from_queue_async("t1"))
    assert resumed.data["b"] == 2
    assert not queue.pending()


def test_review_server_endpoints():
    queue = InMemoryReviewQueue()
    engine = _build_engine(queue)
    asyncio.run(engine.run_async(GraphState(), thread_id="t2"))
    server, endpoint = _start_server(engine, queue)

    resp = requests.get(f"{endpoint}/tasks")
    assert resp.status_code == 200
    assert "t2" in resp.json()

    resp = requests.post(f"{endpoint}/tasks/t2/approve")
    assert resp.status_code == 200
    assert resp.json()["result"]["data"]["b"] == 2

    asyncio.run(engine.run_async(GraphState(), thread_id="t3"))
    resp = requests.post(f"{endpoint}/tasks/t3/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED_BY_HUMAN"
