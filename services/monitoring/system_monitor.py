from __future__ import annotations

from typing import Dict

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter


class SystemMonitor:
    """Collect system metrics and traces using OpenTelemetry."""

    def __init__(
        self, metrics_collector: MetricReader, trace_exporter: SpanExporter
    ) -> None:
        """Initialize monitoring with OpenTelemetry integration."""
        meter_provider = MeterProvider(metric_readers=[metrics_collector])
        metrics.set_meter_provider(meter_provider)
        self._meter = metrics.get_meter(__name__)

        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        self._tracer = trace.get_tracer(__name__)

        self._task_time = self._meter.create_histogram(
            "agent.task_completion_time",
            unit="s",
            description="Task completion time",
        )
        self._resource_usage = self._meter.create_histogram(
            "agent.resource_consumption",
            description="Resource consumption",
        )
        self._quality_score = self._meter.create_histogram(
            "agent.quality_score",
            description="Quality scores",
        )
        self._error_counter = self._meter.create_counter(
            "agent.error_count", description="Error count"
        )
        self._collab_effectiveness = self._meter.create_histogram(
            "agent.collaboration_effectiveness",
            description="Collaboration effectiveness",
        )

    def track_agent_performance(self, agent_id: str, task_metrics: Dict) -> None:
        """Record agent performance data for analysis."""
        attributes = {"agent_id": agent_id}
        with self._tracer.start_as_current_span(
            "agent_performance", attributes=attributes
        ) as span:
            time = task_metrics.get("task_completion_time")
            if time is not None:
                self._task_time.record(time, attributes)
                span.set_attribute("task_completion_time", time)

            resources = task_metrics.get("resource_consumption")
            if resources is not None:
                self._resource_usage.record(resources, attributes)
                span.set_attribute("resource_consumption", resources)

            quality = task_metrics.get("quality_score")
            if quality is not None:
                self._quality_score.record(quality, attributes)
                span.set_attribute("quality_score", quality)

            errors = task_metrics.get("error_rate")
            if errors is not None:
                self._error_counter.add(errors, attributes)
                span.set_attribute("error_rate", errors)

            collab = task_metrics.get("collaboration_effectiveness")
            if collab is not None:
                self._collab_effectiveness.record(collab, attributes)
                span.set_attribute("collaboration_effectiveness", collab)
