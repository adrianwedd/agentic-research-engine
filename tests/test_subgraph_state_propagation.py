import asyncio
from threading import Thread

from agents.memory_manager import MemoryManagerAgent
from engine.orchestration_engine import GraphState, create_orchestration_engine
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer
from services.tool_registry import create_default_registry


def _start_server():
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_subgraph_propagation_and_continuity():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint, tool_registry=create_default_registry())

    engine = create_orchestration_engine(memory_manager=mm)

    def step_one(state: GraphState, sp: dict) -> GraphState:
        state.data["entities"] = [{"id": "E1"}]
        return state

    def step_two(state: GraphState, sp: dict) -> GraphState:
        state.data.setdefault("entities", []).append({"id": "E2"})
        state.data["relations"] = [
            {"subject": "E1", "predicate": "LINKS_TO", "object": "E2"}
        ]
        return state

    engine.add_node("A", step_one)
    engine.add_node("B", step_two)
    engine.add_edge("A", "B")

    final = asyncio.run(engine.run_async(GraphState()))
    assert {"id": "E1"} in final.data["entities"]
    assert {"id": "E2"} in final.data["entities"]

    stored = server.service.retrieve(
        "semantic",
        {"subject": "E1", "predicate": "LINKS_TO", "object": "E2"},
    )
    assert stored
    server.httpd.shutdown()
