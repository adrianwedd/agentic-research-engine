import json
from pathlib import Path

import pytest
import yaml
from jsonschema_path import SchemaPath
from openapi_core import OpenAPI
from openapi_core.shortcuts import validate_request
from openapi_core.testing.requests import MockRequest

SPEC = OpenAPI(
    SchemaPath.from_dict(yaml.safe_load(Path("docs/api/openapi.yaml").read_text()))
).spec

CASES = [
    ("ltm_contract/consolidate_success.json", "post", "/memory", True),
    ("ltm_contract/consolidate_missing_record.json", "post", "/memory", False),
    ("ltm_contract/retrieve_success.json", "get", "/memory", True),
    ("procedural_contract/procedure_store_success.json", "post", "/memory", True),
    ("procedural_contract/procedure_retrieve_success.json", "get", "/memory", True),
]


def _build_request(case_file: str, method: str, path: str) -> MockRequest:
    case_path = Path("tests/fixtures") / case_file
    payload = json.loads(case_path.read_text())
    req = payload.get("request", {})
    headers = req.get("headers")
    params = req.get("params")
    body = req.get("json")
    data = json.dumps(body).encode() if body is not None else b""
    return MockRequest(
        "http://test", method, path, args=params, headers=headers, data=data
    )


@pytest.mark.parametrize("case_file,method,path,is_valid", CASES)
def test_case_schema(case_file: str, method: str, path: str, is_valid: bool) -> None:
    request = _build_request(case_file, method, path)
    if is_valid:
        validate_request(request, SPEC)
    else:
        with pytest.raises(Exception):
            validate_request(request, SPEC)
