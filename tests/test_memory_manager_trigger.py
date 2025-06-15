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


def test_memory_manager_invoked_after_graph():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint, tool_registry=create_default_registry())

    engine = create_orchestration_engine(memory_manager=mm)
    engine.add_node("A", lambda s: s)

    state = GraphState(data={"query": "Write docs"})
    asyncio.run(engine.run_async(state))

    # memory should be stored via the HTTP service
    mem = server.service.retrieve("episodic", {"query": "Write docs"})
    assert mem
    server.httpd.shutdown()
