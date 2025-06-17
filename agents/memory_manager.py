from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from engine.state import State
from services import load_llm_client
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
        """Extract knowledge triples from ``state.data['report']`` using an LLM.

        The LLM may return nested structures grouping multiple relations under a
        single subject. This method flattens such structures so callers always
        receive a list of ``{"subject", "predicate", "object", "properties"}``
        dictionaries.
        """
        text = state.data.get("report", "")
        if not isinstance(text, str):
            return []

        client = load_llm_client()
        system_msg = (
            "You are a knowledge extraction engine. "
            "Extract all factual relationships as JSON array of objects "
            "with 'subject', 'predicate', 'object' and optional 'properties'. "
            "Nested relation groups are allowed using a 'relations' array."
        )
        examples = [
            (
                "Apple acquired NeXT in 1997.",
                [
                    {
                        "subject": "Apple",
                        "predicate": "ACQUIRED",
                        "object": "NeXT",
                        "properties": {"year": 1997},
                    }
                ],
            ),
            (
                "The framework, developed by the core team in California, was released under the Apache 2.0 license.",
                [
                    {
                        "subject": "framework",
                        "predicate": "DEVELOPED_BY",
                        "object": "core team",
                    },
                    {
                        "subject": "core team",
                        "predicate": "LOCATED_IN",
                        "object": "California",
                    },
                    {
                        "subject": "framework",
                        "predicate": "LICENSED_UNDER",
                        "object": "Apache 2.0 license",
                    },
                ],
            ),
        ]
        messages = [{"role": "system", "content": system_msg}]
        for ex_text, triples in examples:
            messages.append({"role": "user", "content": ex_text})
            messages.append({"role": "assistant", "content": json.dumps(triples)})
        messages.append({"role": "user", "content": text})

        try:
            resp = client.invoke(messages)
            data = json.loads(resp)

            triples: List[Dict[str, Any]] = []

            def _collect(item: Any, subject: Optional[str] = None) -> None:
                if isinstance(item, dict):
                    if {"subject", "predicate", "object"} <= item.keys():
                        triples.append(item)
                    elif "subject" in item and "relations" in item:
                        subj = item["subject"]
                        for rel in item.get("relations", []):
                            _collect(rel, subj)
                    elif subject and {"predicate", "object"} <= item.keys():
                        triple = {
                            "subject": subject,
                            "predicate": item["predicate"],
                            "object": item["object"],
                        }
                        if "properties" in item:
                            triple["properties"] = item["properties"]
                        triples.append(triple)
                elif isinstance(item, list):
                    for sub in item:
                        _collect(sub, subject)

            _collect(data)
            return triples
        except Exception:  # pragma: no cover - log only
            logger.exception("LLM relation extraction failed")
            return []

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
