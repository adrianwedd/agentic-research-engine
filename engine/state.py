from __future__ import annotations

from typing import Any, Dict, List

from opentelemetry import trace
from pydantic import BaseModel, Field


class State(BaseModel):
    """Central state passed between orchestration nodes."""

    data: Dict[str, Any] = Field(default_factory=dict)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    status: str | None = None
    evaluator_feedback: Dict[str, Any] | None = None
    retry_count: int = 0

    def update(self, other: Dict[str, Any]) -> None:
        """Merge arbitrary key-value pairs into ``data`` and record the change."""
        self.data.update(other)
        self.history.append({"action": "update", "data": other})
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "state.update",
            attributes={
                "action": "update",
                "keys": ",".join(other.keys()),
            },
        ):
            pass

    def add_message(self, message: Dict[str, Any]) -> None:
        """Append a message and log it in ``history``."""
        self.messages.append(message)
        self.history.append({"action": "add_message", "message": message})
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "state.update",
            attributes={
                "action": "add_message",
                "message_type": str(message.get("type", "message")),
            },
        ):
            pass

    def to_json(self) -> str:  # pragma: no cover - thin wrapper
        return self.model_dump_json()

    @classmethod
    def from_json(cls, payload: str) -> "State":  # pragma: no cover - thin wrapper
        return cls.model_validate_json(payload)

    def __getitem__(self, item: str):
        return getattr(self, item)
