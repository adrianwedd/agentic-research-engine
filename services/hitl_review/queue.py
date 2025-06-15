from __future__ import annotations

from typing import Dict, Tuple

from engine.state import State


class InMemoryReviewQueue:
    """Store paused tasks awaiting human review."""

    def __init__(self) -> None:
        self._queue: Dict[str, Tuple[State, str | None]] = {}

    def enqueue(self, run_id: str, state: State, next_node: str | None) -> None:
        self._queue[run_id] = (state, next_node)

    def pop(self, run_id: str) -> Tuple[State, str | None]:
        return self._queue.pop(run_id)

    def get(self, run_id: str) -> Tuple[State, str | None]:
        return self._queue[run_id]

    def pending(self) -> list[str]:
        return list(self._queue.keys())
