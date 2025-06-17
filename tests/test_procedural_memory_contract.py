import json
from pathlib import Path
from threading import Thread

import requests

from services.ltm_service import (
    EpisodicMemoryService,
    InMemoryStorage,
    LTMService,
    LTMServiceServer,
    ProceduralMemoryService,
)

FIXTURE_DIR = Path("tests/fixtures/procedural_contract")


def _start_server() -> tuple[LTMServiceServer, str]:
    episodic = EpisodicMemoryService(InMemoryStorage())
    procedural = ProceduralMemoryService(InMemoryStorage())
    service = LTMService(episodic, procedural_memory=procedural)
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def _load_case(name: str) -> dict:
    path = FIXTURE_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _assert_contract(resp: requests.Response, expected: dict) -> None:
    assert resp.status_code == expected["status"]
    body = resp.json()
    for key, value in expected.get("body", {}).items():
        if value == "*":
            assert key in body
        else:
            assert body.get(key) == value


def test_store_and_execute_procedure():
    server, endpoint = _start_server()
    case_store = _load_case("procedure_store_success")
    resp = requests.post(
        f"{endpoint}/memory",
        headers=case_store["request"].get("headers", {}),
        json=case_store["request"].get("json"),
    )
    _assert_contract(resp, case_store["response"])
    proc_id = resp.json()["id"]

    case_retrieve = _load_case("procedure_retrieve_success")
    resp = requests.get(
        f"{endpoint}/memory",
        headers=case_retrieve["request"].get("headers", {}),
        params=case_retrieve["request"].get("params"),
        json=case_retrieve["request"].get("json"),
    )
    _assert_contract(resp, case_retrieve["response"])

    output = server.service._modules["procedural"].execute_procedure(proc_id)
    assert output == [3]
    server.httpd.shutdown()
