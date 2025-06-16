from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from engine.state import State
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
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.pass_threshold = pass_threshold
        self.novelty_threshold = novelty_threshold
        self.tool_registry = tool_registry or create_default_registry()

    def _quality_passed(self, state: State) -> bool:
        return True

    def _is_novel(self, record: Dict[str, Any]) -> bool:
        return True

    def _format_record(self, state: State) -> Dict[str, Any]:
        return {
            "task_context": state.data,
            "execution_trace": {"messages": state.messages, "history": state.history},
            "outcome": {"status": state.status},
        }

    def _extract_triples(self, state: State) -> List[Dict[str, Any]]:
        """Very simple pattern-based relation extraction for demo purposes."""
        text = state.data.get("report", "")
        if not isinstance(text, str):
            return []
        triples: List[Dict[str, Any]] = []
        pattern = re.compile(
            r"(?P<subject>[A-Z][A-Za-z0-9& ]+) acquired (?P<object>[A-Z][A-Za-z0-9& ]+) in (?P<year>\d{4})",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            triples.append(
                {
                    "subject": match.group("subject"),
                    "predicate": "ACQUIRED",
                    "object": match.group("object"),
                    "properties": {"year": int(match.group("year"))},
                }
            )
        return triples

    def __call__(self, state: State, scratchpad: Dict[str, Any]) -> State:
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
            for triple in self._extract_triples(state):
                self.tool_registry.invoke(
                    "MemoryManager",
                    "consolidate_memory",
                    triple,
                    memory_type="semantic",
                    endpoint=self.endpoint,
                )
        except Exception:  # pragma: no cover - log only
            logger.exception("Failed to consolidate memory")
        return state
