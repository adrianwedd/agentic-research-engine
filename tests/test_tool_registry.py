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

from services.tool_registry import (
    AccessDeniedError,
    ToolRegistry,
    ToolRegistryAsyncClient,
)
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
            f"{endpoint}/tool",
            params={"agent": "Supervisor", "name": "dummy"},
            headers={"X-User": "alice"},
        )
        assert any(
            json.loads(record.message).get("role") == "Supervisor"
            and json.loads(record.message).get("user") == "alice"
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


def test_tool_invocation_audit_logged(caplog):
    registry = ToolRegistry()

    def tool(x):
        return x

    registry.register_tool("dummy", tool)
    with caplog.at_level("INFO"):
        out = registry.invoke("WebResearcher", "dummy", "hi", intent="demo")
    assert out == "hi"
    entries = [json.loads(r.message) for r in caplog.records]
    assert any(
        e.get("outcome") == "success" and e.get("action") == "dummy" for e in entries
    )


def test_tool_invocation_audit_blocked(caplog):
    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool, allowed_roles=["Other"])
    with caplog.at_level("INFO"):
        with pytest.raises(AccessDeniedError):
            registry.invoke("WebResearcher", "dummy", intent="demo")
    entries = [json.loads(r.message) for r in caplog.records]
    assert any(e.get("outcome") == "blocked" for e in entries)


def test_tool_init_failure_recorded():
    exporter = InMemorySpanExporter()
    trace.set_tracer_provider(TracerProvider())
    provider = trace.get_tracer_provider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    registry = ToolRegistry()

    class FailingDict(dict):
        def __setitem__(self, key, value):  # pragma: no cover - triggered in test
            raise RuntimeError("boom")

    registry._tools = FailingDict()

    with pytest.raises(RuntimeError):
        registry.register_tool("dummy", dummy_tool, allowed_roles=["A"])

    span = next(s for s in exporter.spans if s.name == "tool.init")
    assert span.attributes.get("init.failed") is True
    assert span.attributes.get("allowed_roles") == "A"
    assert any(evt.name == "exception" for evt in span.events)


@pytest.mark.asyncio
async def test_async_client_interaction(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text("permissions:\n  dummy:\n    - WebResearcher\n")

    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool)
    registry.load_permissions(str(config))
    server = ToolRegistryServer(registry, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    client = ToolRegistryAsyncClient(endpoint)
    try:
        tool = await client.get_tool("WebResearcher", "dummy")
        assert tool == "dummy"
        with pytest.raises(AccessDeniedError):
            await client.get_tool("Supervisor", "dummy")
    finally:
        await client.close()
        server.httpd.shutdown()
        thread.join()
