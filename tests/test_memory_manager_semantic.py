import json
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


def test_knowledge_graph_population(monkeypatch):
    server, endpoint = _start_server()

    class DummyClient:
        def invoke(self, _messages, **_kwargs):
            return json.dumps(
                [
                    {
                        "subject": "framework",
                        "predicate": "DEVELOPED_BY",
                        "object": "core team",
                    },
                    {
                        "subject": "core team",
                        "predicate": "LOCATED_IN",
                        "object": "California",
                    },
                    {
                        "subject": "framework",
                        "predicate": "LICENSED_UNDER",
                        "object": "Apache 2.0 license",
                    },
                ]
            )

    monkeypatch.setattr("agents.memory_manager.load_llm_client", lambda: DummyClient())

    mm = MemoryManagerAgent(endpoint=endpoint)
    text = (
        "The framework, developed by the core team in California, "
        "was released under the Apache 2.0 license."
    )
    state = GraphState(data={"report": text})
    state.evaluator_feedback = {"overall_score": 1.0}
    mm(state, {})

    dev = server.service.retrieve(
        "semantic",
        {"subject": "framework", "predicate": "DEVELOPED_BY", "object": "core team"},
        limit=1,
    )
    loc = server.service.retrieve(
        "semantic",
        {"subject": "core team", "predicate": "LOCATED_IN", "object": "California"},
        limit=1,
    )
    lic = server.service.retrieve(
        "semantic",
        {
            "subject": "framework",
            "predicate": "LICENSED_UNDER",
            "object": "Apache 2.0 license",
        },
        limit=1,
    )

    assert dev and loc and lic
    server.httpd.shutdown()
