from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from engine.state import State
from services.tool_registry import ToolRegistry, create_default_registry

logger = logging.getLogger(__name__)


class MemoryManagerAgent:
    """Agent responsible for consolidating task episodes into LTM."""

    def __init__(
        self,
        *,
        endpoint: Optional[str] = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.tool_registry = tool_registry or create_default_registry()

    def _format_record(self, state: State) -> Dict[str, Any]:
        return {
            "task_context": state.data,
            "execution_trace": {"messages": state.messages, "history": state.history},
            "outcome": {"status": state.status},
        }

    def __call__(self, state: State, scratchpad: Dict[str, Any]) -> State:
        record = self._format_record(state)
        try:
            self.tool_registry.invoke(
                "MemoryManager",
                "consolidate_memory",
                record,
                endpoint=self.endpoint,
            )
        except Exception:  # pragma: no cover - log only
            logger.exception("Failed to consolidate memory")
        return state
