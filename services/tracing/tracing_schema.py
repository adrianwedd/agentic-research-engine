from __future__ import annotations

"""Versioned tracing schema for agent actions."""

from dataclasses import dataclass
from typing import Any, Optional

from opentelemetry import trace

SCHEMA_VERSION = "1.0"


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

    def record(self) -> None:
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "tool_call",
            attributes={
                "schema_version": SCHEMA_VERSION,
                "agent_id": self.agent_id,
                "agent_role": self.agent_role,
                "tool_name": self.tool_name,
                "tool_input": str(self.tool_input),
            },
        ) as span:
            if self.tool_output is not None:
                span.set_attribute("tool_output", str(self.tool_output))
            if self.input_tokens is not None:
                span.set_attribute("input_tokens", self.input_tokens)
            if self.output_tokens is not None:
                span.set_attribute("output_tokens", self.output_tokens)
            if self.latency_ms is not None:
                span.set_attribute("latency_ms", self.latency_ms)
