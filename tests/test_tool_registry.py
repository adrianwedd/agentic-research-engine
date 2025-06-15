from threading import Thread

import pytest
import requests

from services.tool_registry import AccessDeniedError, ToolRegistry
from services.tool_registry.registry import ToolRegistryServer


def dummy_tool():
    return "ok"


def test_registry_authorization():
    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool, allowed_roles=["WebResearcher"])

    tool = registry.get_tool("WebResearcher", "dummy")
    assert tool() == "ok"

    with pytest.raises(AccessDeniedError):
        registry.get_tool("Supervisor", "dummy")


def test_registry_server_permissions(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text("permissions:\n  dummy:\n    - WebResearcher\n")

    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool)
    registry.load_permissions(str(config))
    server = ToolRegistryServer(registry, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    try:
        resp = requests.get(
            f"{endpoint}/tool", params={"agent": "WebResearcher", "name": "dummy"}
        )
        assert resp.status_code == 200
        assert resp.json() == {"tool": "dummy"}

        resp = requests.get(
            f"{endpoint}/tool", params={"agent": "Supervisor", "name": "dummy"}
        )
        assert resp.status_code == 403
        assert "cannot access" in resp.json()["error"]
    finally:
        server.httpd.shutdown()
        thread.join()
