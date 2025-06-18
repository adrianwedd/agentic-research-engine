from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService
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


def test_ltm_hit_and_miss_metrics(monkeypatch):
    import importlib

    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as trace

    importlib.reload(trace)
    importlib.reload(metrics_internal)
    metric_reader = InMemoryMetricReader()
    span_exporter = InMemorySpanExporter()
    monitor = SystemMonitor(metric_reader, span_exporter)
    service = LTMService(EpisodicMemoryService(InMemoryStorage()), monitor=monitor)

    service.consolidate(
        "episodic",
        {"task_context": {"desc": "x"}, "execution_trace": {}, "outcome": {}},
    )
    service.retrieve("episodic", {"desc": "x"})  # hit
    service.retrieve("semantic", {"subject": "nope"})  # miss

    data = metric_reader.get_metrics_data()
    names = {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }
    assert "ltm.hits" in names
    assert "ltm.misses" in names


def test_ltm_deletion_metric(monkeypatch):
    import importlib

    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as trace

    importlib.reload(trace)
    importlib.reload(metrics_internal)
    metric_reader = InMemoryMetricReader()
    span_exporter = InMemorySpanExporter()
    monitor = SystemMonitor(metric_reader, span_exporter)

    monitor.record_ltm_deletions(3)

    data = metric_reader.get_metrics_data()
    names = {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }
    assert "ltm.deletions" in names
