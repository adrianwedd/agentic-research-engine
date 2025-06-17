from __future__ import annotations

import os
from typing import Dict

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter


class SystemMonitor:
    """Collect system metrics and traces using OpenTelemetry."""

    def __init__(
        self, metrics_collector: MetricReader, trace_exporter: SpanExporter
    ) -> None:
        """Initialize monitoring with OpenTelemetry integration."""
        resource = Resource.create(
            {
                "service.name": "system-monitor",
                "environment": os.getenv("ENVIRONMENT", "dev"),
                "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
            }
        )

        meter_provider = MeterProvider(
            metric_readers=[metrics_collector], resource=resource
        )
        metrics.set_meter_provider(meter_provider)
        self._meter = metrics.get_meter(__name__)

        tracer_provider = TracerProvider(resource=resource)
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
        self._ltm_hit_counter = self._meter.create_counter(
            "ltm.hits", description="LTM retrieval hits"
        )
        self._ltm_miss_counter = self._meter.create_counter(
            "ltm.misses", description="LTM retrieval misses"
        )

    @classmethod
    def from_otlp(cls, endpoint: str = "http://localhost:4317") -> "SystemMonitor":
        """Instantiate a monitor that exports via OTLP to the given endpoint."""
        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        metric_reader = PeriodicExportingMetricReader(metric_exporter)
        span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        return cls(metric_reader, span_exporter)

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

    def record_ltm_result(self, memory_type: str, hit: bool) -> None:
        """Record the outcome of an LTM lookup."""
        attributes = {"memory_type": memory_type}
        if hit:
            self._ltm_hit_counter.add(1, attributes)
        else:
            self._ltm_miss_counter.add(1, attributes)
