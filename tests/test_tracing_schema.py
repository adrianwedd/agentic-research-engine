from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from agents.web_researcher import WebResearcherAgent
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


def test_web_search_tool_emits_trace_span():
    exporter = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.add_span_processor(SimpleSpanProcessor(exporter))

    def web_search(query):
        return [{"url": "http://example.com", "title": "t"}]

    registry = {
        "web_search": web_search,
        "summarize": lambda text: "s",
        "pdf_extract": None,
        "html_scraper": None,
        "assess_source": lambda url: 1.0,
    }

    agent = WebResearcherAgent(registry)
    agent.research_topic("q", {"agent_id": "A1"})

    assert exporter.spans
    span = exporter.spans[0]
    assert span.attributes["agent_id"] == "A1"
    assert span.attributes["agent_role"] == "WebResearcher"
    assert span.attributes["tool_name"] == "web_search"
    assert span.attributes["tool_input"] == "q"
    assert span.attributes["tool_output"] == str(
        [{"url": "http://example.com", "title": "t"}]
    )
    assert span.attributes["input_tokens"] == 1
    assert span.attributes["output_tokens"] >= 1
    assert span.attributes["latency_ms"] >= 0


def test_parse_old_schema_version():
    attrs = {
        "schema_version": "1.0",
        "agent_id": "A1",
        "agent_role": "WebResearcher",
        "tool_name": "web_search",
        "tool_input": "q",
        "tool_output": "result",
    }

    trace_obj = ToolCallTrace.from_attributes(attrs)
    assert trace_obj.agent_id == "A1"
    assert trace_obj.tool_name == "web_search"
    assert trace_obj.schema_version == "1.0"
