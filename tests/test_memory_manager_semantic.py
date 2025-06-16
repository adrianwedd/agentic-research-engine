from threading import Thread

from agents.memory_manager import MemoryManagerAgent
from engine.orchestration_engine import GraphState
from services.ltm_service import (
    EpisodicMemoryService,
    InMemoryStorage,
    LTMService,
    LTMServiceServer,
)


def _start_server():
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_knowledge_graph_population():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint)
    state = GraphState(data={"report": "Apple acquired NeXT in 1997"})
    state.evaluator_feedback = {"overall_score": 1.0}
    mm(state, {})
    facts = server.service.retrieve(
        "semantic",
        {"subject": "Apple", "predicate": "ACQUIRED", "object": "NeXT"},
        limit=1,
    )
    assert facts
    fact = facts[0]
    assert fact["subject"] == "Apple"
    assert fact["object"] == "NeXT"
    assert fact["predicate"] == "ACQUIRED"
    assert fact["properties"].get("year") == 1997
    server.httpd.shutdown()
