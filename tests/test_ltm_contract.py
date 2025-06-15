import json
from pathlib import Path
from threading import Thread

import pytest
import requests

from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer

FIXTURE_DIR = Path("tests/fixtures/ltm_contract")


def _start_server() -> tuple[LTMServiceServer, str]:
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
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


@pytest.fixture()
def ltm_endpoint():
    server, endpoint = _start_server()
    yield endpoint
    server.httpd.shutdown()


def test_consolidate_success_contract(ltm_endpoint):
    case = _load_case("consolidate_success")
    resp = requests.post(
        f"{ltm_endpoint}/memory",
        headers=case["request"].get("headers", {}),
        json=case["request"].get("json"),
    )
    _assert_contract(resp, case["response"])

    # ensure retrieval works for subsequent test
    case_retrieve = _load_case("retrieve_success")
    resp = requests.get(
        f"{ltm_endpoint}/memory",
        headers=case_retrieve["request"].get("headers", {}),
        params=case_retrieve["request"].get("params"),
        json=case_retrieve["request"].get("json"),
    )
    _assert_contract(resp, case_retrieve["response"])


def test_consolidate_missing_record_contract(ltm_endpoint):
    case = _load_case("consolidate_missing_record")
    resp = requests.post(
        f"{ltm_endpoint}/memory",
        headers=case["request"].get("headers", {}),
        json=case["request"].get("json"),
    )
    _assert_contract(resp, case["response"])


def test_consolidate_invalid_memory_type_contract(ltm_endpoint):
    case = _load_case("consolidate_invalid_memory_type")
    resp = requests.post(
        f"{ltm_endpoint}/memory",
        headers=case["request"].get("headers", {}),
        json=case["request"].get("json"),
    )
    _assert_contract(resp, case["response"])


def test_consolidate_invalid_role_contract(ltm_endpoint):
    case = _load_case("consolidate_invalid_role")
    resp = requests.post(
        f"{ltm_endpoint}/memory",
        headers=case["request"].get("headers", {}),
        json=case["request"].get("json"),
    )
    _assert_contract(resp, case["response"])


def test_retrieve_invalid_memory_type_contract(ltm_endpoint):
    case = _load_case("retrieve_invalid_memory_type")
    resp = requests.get(
        f"{ltm_endpoint}/memory",
        headers=case["request"].get("headers", {}),
        params=case["request"].get("params"),
        json=case["request"].get("json"),
    )
    _assert_contract(resp, case["response"])


def test_retrieve_invalid_role_contract(ltm_endpoint):
    case = _load_case("retrieve_invalid_role")
    resp = requests.get(
        f"{ltm_endpoint}/memory",
        headers=case["request"].get("headers", {}),
        json=case["request"].get("json"),
    )
    _assert_contract(resp, case["response"])
