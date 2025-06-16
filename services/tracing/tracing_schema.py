from __future__ import annotations

"""Versioned tracing schema for agent actions."""

from dataclasses import dataclass
from typing import Any, Optional

from opentelemetry import trace

from . import increment_metric

SCHEMA_VERSION = "1.1"


@dataclass
class ToolCallTrace:
    agent_id: str
    agent_role: str
    tool_name: str
    tool_input: Any
    tool_output: Any | None = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    intent: Optional[str] = None
    unauthorized_call: Optional[bool] = None
    schema_version: str = SCHEMA_VERSION

    def record(self) -> None:
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "tool_call",
            attributes={
                "schema_version": self.schema_version,
                "agent_id": self.agent_id,
                "agent_role": self.agent_role,
                "tool_name": self.tool_name,
                "tool_input": str(self.tool_input),
                "intent": self.intent or "",
                "unauthorized_call": bool(self.unauthorized_call),
            },
        ) as span:
            if self.tool_output is not None:
                span.set_attribute("tool_output", str(self.tool_output))
            if self.input_tokens is not None:
                span.set_attribute("input_tokens", self.input_tokens)
                increment_metric("total_tokens_consumed", float(self.input_tokens))
            if self.output_tokens is not None:
                span.set_attribute("output_tokens", self.output_tokens)
                increment_metric("total_tokens_consumed", float(self.output_tokens))
            if self.latency_ms is not None:
                span.set_attribute("latency_ms", self.latency_ms)
            increment_metric("tool_call_count", 1.0)

    @classmethod
    def from_attributes(cls, attrs: dict[str, Any]) -> "ToolCallTrace":
        """Create a :class:`ToolCallTrace` from span attributes."""
        version = attrs.get("schema_version", "1.0")
        return cls(
            agent_id=str(attrs.get("agent_id", "")),
            agent_role=str(attrs.get("agent_role", "")),
            tool_name=str(attrs.get("tool_name", "")),
            tool_input=attrs.get("tool_input"),
            tool_output=attrs.get("tool_output"),
            input_tokens=attrs.get("input_tokens"),
            output_tokens=attrs.get("output_tokens"),
            latency_ms=attrs.get("latency_ms"),
            intent=attrs.get("intent"),
            unauthorized_call=attrs.get("unauthorized_call"),
            schema_version=version,
        )
