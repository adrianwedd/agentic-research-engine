import json
from threading import Thread

import pytest
import requests
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from services.tool_registry import AccessDeniedError, ToolRegistry
from services.tool_registry.registry import ToolRegistryServer
from services.tracing.tracing_schema import ToolCallTrace


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - not needed
        pass

    def force_flush(
        self, timeout_millis: int = 30_000
    ) -> bool:  # pragma: no cover - not needed
        return True


def dummy_tool():
    return "ok"


def test_registry_authorization():
    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool, allowed_roles=["WebResearcher"])

    assert registry.invoke("WebResearcher", "dummy") == "ok"

    with pytest.raises(AccessDeniedError):
        registry.invoke("Supervisor", "dummy")


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


def test_registry_server_logs_denied_access(tmp_path, caplog):
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
        caplog.set_level("WARNING")
        requests.get(
            f"{endpoint}/tool", params={"agent": "Supervisor", "name": "dummy"}
        )
        assert any(
            json.loads(record.message).get("role") == "Supervisor"
            for record in caplog.records
        )
    finally:
        server.httpd.shutdown()
        thread.join()


def test_tool_init_span_and_propagation():
    exporter = InMemorySpanExporter()
    trace.set_tracer_provider(TracerProvider())
    provider = trace.get_tracer_provider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    registry = ToolRegistry()

    def tool(x):
        return x

    registry.register_tool("dummy", tool)
    wrapped = registry.get_tool("WebResearcher", "dummy")
    out = wrapped("hi")
    ToolCallTrace(
        agent_id="A",
        agent_role="WebResearcher",
        tool_name="dummy",
        tool_input="hi",
        tool_output=out,
    ).record()

    names = {span.name for span in exporter.spans}
    assert "tool.init" in names
    assert "tool_call" in names
