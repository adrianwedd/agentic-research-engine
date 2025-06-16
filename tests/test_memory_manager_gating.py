from threading import Thread

from agents.memory_manager import MemoryManagerAgent
from engine.orchestration_engine import GraphState
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer


def _start_server():
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_quality_gate_blocks_consolidation():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint, pass_threshold=0.5)
    state = GraphState(data={"query": "Q"})
    state.evaluator_feedback = {"overall_score": 0.2}
    mm(state)
    assert not server.service.retrieve("episodic", {"query": "Q"})
    server.httpd.shutdown()


def test_novelty_gate_blocks_duplicates():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint, novelty_threshold=0.95)
    # store existing memory
    server.service.consolidate(
        "episodic",
        {
            "task_context": {"query": "D"},
            "execution_trace": {},
            "outcome": {"success": True},
        },
    )
    state = GraphState(data={"query": "D"})
    state.evaluator_feedback = {"overall_score": 1.0}
    mm(state)
    mems = server.service.retrieve("episodic", {"query": "D"})
    assert len(mems) == 1
    server.httpd.shutdown()


def test_high_quality_novel_memory_consolidated():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint)
    state = GraphState(data={"query": "N"})
    state.evaluator_feedback = {"overall_score": 1.0}
    mm(state)
    mems = server.service.retrieve("episodic", {"query": "N"})
    assert mems
    server.httpd.shutdown()
