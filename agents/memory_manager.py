from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from engine.state import State
from tools.ltm_client import consolidate_memory

logger = logging.getLogger(__name__)


class MemoryManagerAgent:
    """Agent responsible for consolidating task episodes into LTM."""

    def __init__(self, *, endpoint: Optional[str] = None) -> None:
        self.endpoint = endpoint

    def _format_record(self, state: State) -> Dict[str, Any]:
        return {
            "task_context": state.data,
            "execution_trace": {"messages": state.messages, "history": state.history},
            "outcome": {"status": state.status},
        }

    def __call__(self, state: State) -> State:
        record = self._format_record(state)
        try:
            consolidate_memory(record, endpoint=self.endpoint)
        except Exception:  # pragma: no cover - log only
            logger.exception("Failed to consolidate memory")
        return state
