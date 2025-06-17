from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional


@dataclass
class EvaluationCompletedEvent:
    task_id: str
    worker_agent_id: str
    evaluator_id: str
    performance_vector: Dict[str, Any]
    task_type: Optional[str] = None
    is_final: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


_event_queue: asyncio.Queue[EvaluationCompletedEvent] = asyncio.Queue()


def publish_event(event: EvaluationCompletedEvent) -> None:
    """Publish an evaluation completed event."""
    _event_queue.put_nowait(event)


async def event_stream() -> AsyncIterator[EvaluationCompletedEvent]:
    """Yield events as they are published."""
    while True:
        event = await _event_queue.get()
        yield event
