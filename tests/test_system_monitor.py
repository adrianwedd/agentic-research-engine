from __future__ import annotations

from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from services.monitoring.system_monitor import SystemMonitor


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True


def test_track_agent_performance_records_metrics_and_span():
    metric_reader = InMemoryMetricReader()
    span_exporter = InMemorySpanExporter()
    monitor = SystemMonitor(metric_reader, span_exporter)

    monitor.track_agent_performance(
        "agent1",
        {
            "task_completion_time": 2.0,
            "resource_consumption": 10,
            "quality_score": 0.9,
            "error_rate": 0,
            "collaboration_effectiveness": 0.8,
        },
    )

    data = metric_reader.get_metrics_data()
    metric_names = {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }
    assert "agent.task_completion_time" in metric_names
    assert span_exporter.spans
    span = span_exporter.spans[0]
    assert span.attributes["agent_id"] == "agent1"
    assert span.attributes["task_completion_time"] == 2.0
