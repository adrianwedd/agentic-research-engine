from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import List

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter


@dataclass
class AuditLogRecord:
    timestamp: datetime
    agent_id: str
    action: str
    outcome: str


class ActionMonitor:
    """Collect agent actions and tool call metrics."""

    def __init__(
        self, metrics_reader: MetricReader, span_exporter: SpanExporter
    ) -> None:
        resource = Resource.create(
            {
                "service.name": "action-monitor",
                "environment": os.getenv("ENVIRONMENT", "dev"),
                "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
            }
        )
        meter_provider = MeterProvider(
            metric_readers=[metrics_reader], resource=resource
        )
        metrics.set_meter_provider(meter_provider)
        self._meter = metrics.get_meter(__name__)

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        self._tracer = trace.get_tracer(__name__)

        self._action_counter = self._meter.create_counter(
            "agent.actions", description="Count of agent actions"
        )
        self._tool_counter = self._meter.create_counter(
            "agent.tool_calls", description="Count of tool calls"
        )
        self.logs: List[AuditLogRecord] = []

    @classmethod
    def from_otlp(cls, endpoint: str = "http://localhost:4317") -> "ActionMonitor":
        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        reader = PeriodicExportingMetricReader(metric_exporter)
        span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        return cls(reader, span_exporter)

    def record_action(self, agent_id: str, action: str, outcome: str) -> None:
        timestamp = datetime.now(UTC)
        self.logs.append(AuditLogRecord(timestamp, agent_id, action, outcome))
        attrs = {"agent_id": agent_id, "action": action, "outcome": outcome}
        self._action_counter.add(1, attrs)
        with self._tracer.start_as_current_span("agent_action", attributes=attrs):
            pass

    def record_tool_call(self, agent_id: str, tool_name: str, outcome: str) -> None:
        timestamp = datetime.now(UTC)
        self.logs.append(AuditLogRecord(timestamp, agent_id, tool_name, outcome))
        attrs = {"agent_id": agent_id, "tool_name": tool_name, "outcome": outcome}
        self._tool_counter.add(1, attrs)
        with self._tracer.start_as_current_span("tool_call_audit", attributes=attrs):
            pass
