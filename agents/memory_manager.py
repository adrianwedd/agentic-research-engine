from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from engine.state import State
from tools.ltm_client import consolidate_memory, retrieve_memory

from services.tool_registry import ToolRegistry, create_default_registry

logger = logging.getLogger(__name__)


class MemoryManagerAgent:
    """Agent responsible for consolidating task episodes into LTM."""

    def __init__(
        self,
        *,
        endpoint: Optional[str] = None,
        pass_threshold: float = 0.5,
        novelty_threshold: float = 0.9,
    ) -> None:
        self.endpoint = endpoint
        self.pass_threshold = pass_threshold
        self.novelty_threshold = novelty_threshold

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

    def _quality_passed(self, state: State) -> bool:
        if isinstance(state.evaluator_feedback, dict):
            score = float(state.evaluator_feedback.get("overall_score", 0))
            return score >= self.pass_threshold
        if state.status:
            return str(state.status).lower() == "pass"
        return True

    def _is_novel(self, record: Dict[str, Any]) -> bool:
        try:
            results = retrieve_memory(
                record["task_context"],
                memory_type="episodic",
                limit=1,
                endpoint=self.endpoint,
            )
        except Exception:  # pragma: no cover - best effort logging
            logger.exception("Novelty check failed")
            return True
        if not results:
            return True
        similarity = float(results[0].get("similarity", 0))
        return similarity < self.novelty_threshold

    def __call__(self, state: State) -> State:
        record = self._format_record(state)
        if not self._quality_passed(state):
            logger.info("MemoryManager: quality gate failed")
            return state
        if not self._is_novel(record):
            logger.info("MemoryManager: novelty gate failed")
            return state
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
