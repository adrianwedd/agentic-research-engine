from __future__ import annotations

from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from services.monitoring import system_monitor as sm
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


def test_from_otlp_uses_env_metadata(monkeypatch):
    import importlib

    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as trace

    importlib.reload(trace)
    importlib.reload(metrics_internal)
    metric_reader = InMemoryMetricReader()
    span_exporter = InMemorySpanExporter()
    monkeypatch.setattr(
        sm, "OTLPMetricExporter", lambda endpoint, insecure=True: object()
    )
    monkeypatch.setattr(
        sm, "PeriodicExportingMetricReader", lambda exporter: metric_reader
    )
    monkeypatch.setattr(
        sm, "OTLPSpanExporter", lambda endpoint, insecure=True: span_exporter
    )
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SERVICE_VERSION", "1.0.0")

    monitor = SystemMonitor.from_otlp("http://localhost:4317")
    monitor.track_agent_performance("agent", {"task_completion_time": 1})

    assert span_exporter.spans
    span = span_exporter.spans[0]
    assert span.resource.attributes["environment"] == "test"
    assert span.resource.attributes["service.version"] == "1.0.0"
