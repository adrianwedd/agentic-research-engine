from threading import Thread

import requests

from agents.memory_manager import MemoryManagerAgent
from engine.orchestration_engine import GraphState
from services.ltm_service.api import LTMService, LTMServiceServer
from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.semantic_memory import SpatioTemporalMemoryService


def _start_server():
    service = LTMService(
        EpisodicMemoryService(InMemoryStorage()),
        semantic_memory=SpatioTemporalMemoryService(),
    )
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_memory_manager_spatial_query():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint)

    data1 = {
        "subject": "S",
        "predicate": "P",
        "object": "O",
        "value": "v1",
        "valid_from": 0,
        "valid_to": 20,
        "location": {"lat": 1, "lon": 1},
    }
    requests.post(
        f"{endpoint}/temporal_consolidate", json=data1, headers={"X-Role": "editor"}
    )

    data2 = {
        "subject": "S",
        "predicate": "P",
        "object": "O",
        "value": "v2",
        "valid_from": 30,
        "valid_to": 60,
        "location": {"lat": 1.5, "lon": 1.5},
    }
    requests.post(
        f"{endpoint}/temporal_consolidate", json=data2, headers={"X-Role": "editor"}
    )

    state = GraphState(
        data={
            "plan": {
                "bbox": [0, 0, 2, 2],
                "time_range": {"valid_from": 40, "valid_to": 50},
            }
        }
    )
    mm(state)
    ctx = state.data.get("spatial_context")
    assert ctx and ctx[0]["value"] == "v2"
    server.httpd.shutdown()
