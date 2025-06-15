from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class State(BaseModel):
    """Central state passed between orchestration nodes."""

    data: Dict[str, Any] = Field(default_factory=dict)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    status: str | None = None

    def update(self, other: Dict[str, Any]) -> None:
        """Merge arbitrary key-value pairs into ``data``."""
        self.data.update(other)

    def add_message(self, message: Dict[str, Any]) -> None:
        """Append a message to the history."""
        self.messages.append(message)

    def to_json(self) -> str:  # pragma: no cover - thin wrapper
        return self.model_dump_json()

    @classmethod
    def from_json(cls, payload: str) -> "State":  # pragma: no cover - thin wrapper
        return cls.model_validate_json(payload)

    def __getitem__(self, item: str):
        return getattr(self, item)
