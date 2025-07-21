from __future__ import annotations

from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from services.monitoring.action_monitor import ActionMonitor


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):  # type: ignore[override]
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - not needed
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:  # pragma: no cover
        return True


def test_record_action_and_tool_call():
    metric_reader = InMemoryMetricReader()
    span_exporter = InMemorySpanExporter()
    monitor = ActionMonitor(metric_reader, span_exporter)

    monitor.record_action("agent1", "plan", "success")
    monitor.record_tool_call("agent1", "web_search", "success")

    assert len(monitor.logs) == 2

    data = metric_reader.get_metrics_data()
    names = {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }
    assert "agent.actions" in names
    assert "agent.tool_calls" in names
    assert span_exporter.spans
