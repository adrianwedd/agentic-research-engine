import logging
from threading import Thread

import requests

from services.authz import IntentAuthorizer, IntentAuthZServer
from services.tool_registry import ToolRegistry


def dummy_tool():
    return "ok"


def _start_server(policy):
    registry = ToolRegistry()
    registry.register_tool("modify_user", dummy_tool, allowed_roles=["Admin"])
    authorizer = IntentAuthorizer(policy)
    server = IntentAuthZServer(registry, authorizer, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, thread, endpoint


def test_deny_out_of_intent_tool_call(caplog):
    policy = {"intents": {"generate_report": ["retrieve_memory"]}}
    server, thread, endpoint = _start_server(policy)
    try:
        caplog.set_level(logging.WARNING)
        resp = requests.post(
            f"{endpoint}/invoke",
            json={
                "agent": "Admin",
                "intent": "generate_report",
                "tool": "modify_user",
            },
        )
        assert resp.status_code == 403
        assert any("ToolInvocationViolation" in rec.message for rec in caplog.records)
    finally:
        server.httpd.shutdown()
        thread.join()
