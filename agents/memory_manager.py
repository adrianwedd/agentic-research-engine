from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import requests

from engine.state import State
from services import load_llm_client
from services.tool_registry import (
    ToolRegistry,
    ToolRegistryAsyncClient,
    create_default_registry,
)

logger = logging.getLogger(__name__)


class MemoryManagerAgent:
    """Agent responsible for consolidating task episodes into LTM."""

    def __init__(
        self,
        *,
        endpoint: Optional[str] = None,
        ltm_service: Optional[Any] = None,
        pass_threshold: float = 0.5,
        novelty_threshold: float = 0.9,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.ltm_service = ltm_service
        self.pass_threshold = pass_threshold
        self.novelty_threshold = novelty_threshold
        if isinstance(tool_registry, (ToolRegistry, ToolRegistryAsyncClient)):
            self.tool_registry = tool_registry
        else:
            self.tool_registry = tool_registry or create_default_registry()

    # ------------------------------------------------------------------
    # Retrieval helpers
    # ------------------------------------------------------------------
    def _spatial_query(
        self, bbox: List[float], valid_from: float, valid_to: float
    ) -> List[Dict[str, Any]]:
        if self.endpoint:
            try:
                resp = requests.get(
                    f"{self.endpoint}/spatial_query",
                    params={
                        "bbox": ",".join(str(x) for x in bbox),
                        "valid_from": valid_from,
                        "valid_to": valid_to,
                    },
                    headers={"X-Role": "viewer"},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
            except Exception:  # pragma: no cover - log only
                logger.exception("spatial query failed")
                return []
        if self.ltm_service:
            try:
                return self.ltm_service.spatial_query(bbox, valid_from, valid_to)
            except Exception:  # pragma: no cover - log only
                logger.exception("spatial query failed")
        return []

    def _snapshot_query(self, valid_at: float, tx_at: float) -> List[Dict[str, Any]]:
        if self.endpoint:
            try:
                resp = requests.get(
                    f"{self.endpoint}/snapshot",
                    params={"valid_at": valid_at, "tx_at": tx_at},
                    headers={"X-Role": "viewer"},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
            except Exception:  # pragma: no cover - log only
                logger.exception("snapshot query failed")
                return []
        if self.ltm_service:
            try:
                module = self.ltm_service._modules.get("semantic")
                if hasattr(module, "get_snapshot"):
                    return module.get_snapshot(valid_at=valid_at, tx_at=tx_at)
            except Exception:  # pragma: no cover - log only
                logger.exception("snapshot query failed")
        return []

    def _add_skill(self, skill: Dict[str, Any]) -> None:
        if isinstance(self.tool_registry, ToolRegistry):
            self.tool_registry.invoke(
                "MemoryManager",
                "add_skill",
                skill,
                endpoint=self.endpoint,
            )
        elif isinstance(self.tool_registry, ToolRegistryAsyncClient):
            asyncio.run(
                self.tool_registry.invoke(
                    "MemoryManager",
                    "add_skill",
                    skill,
                    endpoint=self.endpoint,
                )
            )

    def _query_skill_vector(self, query: Any, limit: int = 5) -> List[Dict[str, Any]]:
        if isinstance(self.tool_registry, ToolRegistry):
            return self.tool_registry.invoke(
                "MemoryManager",
                "skill_vector_query",
                {"query": query, "limit": limit},
                endpoint=self.endpoint,
            )
        if isinstance(self.tool_registry, ToolRegistryAsyncClient):
            return asyncio.run(
                self.tool_registry.invoke(
                    "MemoryManager",
                    "skill_vector_query",
                    {"query": query, "limit": limit},
                    endpoint=self.endpoint,
                )
            )
        return []

    def _query_skill_metadata(
        self, query: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:
        if isinstance(self.tool_registry, ToolRegistry):
            return self.tool_registry.invoke(
                "MemoryManager",
                "skill_metadata_query",
                {"query": query, "limit": limit},
                endpoint=self.endpoint,
            )
        if isinstance(self.tool_registry, ToolRegistryAsyncClient):
            return asyncio.run(
                self.tool_registry.invoke(
                    "MemoryManager",
                    "skill_metadata_query",
                    {"query": query, "limit": limit},
                    endpoint=self.endpoint,
                )
            )
        return []

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
            if isinstance(self.tool_registry, ToolRegistry):
                self.tool_registry.invoke(
                    "MemoryManager",
                    "consolidate_memory",
                    record,
                    endpoint=self.endpoint,
                )
            elif isinstance(self.tool_registry, ToolRegistryAsyncClient):
                asyncio.run(
                    self.tool_registry.invoke(
                        "MemoryManager",
                        "consolidate_memory",
                        record,
                        endpoint=self.endpoint,
                    )
                )
            skill = state.data.get("skill")
            if isinstance(skill, dict):
                self._add_skill(skill)
            for triple in self._extract_triples(state):
                if isinstance(self.tool_registry, ToolRegistry):
                    self.tool_registry.invoke(
                        "MemoryManager",
                        "semantic_consolidate",
                        {"payload": triple, "format": "jsonld"},
                        endpoint=self.endpoint,
                    )
                elif isinstance(self.tool_registry, ToolRegistryAsyncClient):
                    asyncio.run(
                        self.tool_registry.invoke(
                            "MemoryManager",
                            "semantic_consolidate",
                            {"payload": triple, "format": "jsonld"},
                            endpoint=self.endpoint,
                        )
                    )
            entities = state.data.get("entities")
            relations = state.data.get("relations")
            if isinstance(entities, list) and isinstance(relations, list):
                if isinstance(self.tool_registry, ToolRegistry):
                    self.tool_registry.invoke(
                        "MemoryManager",
                        "propagate_subgraph",
                        {"entities": entities, "relations": relations},
                        endpoint=self.endpoint,
                    )
                elif isinstance(self.tool_registry, ToolRegistryAsyncClient):
                    asyncio.run(
                        self.tool_registry.invoke(
                            "MemoryManager",
                            "propagate_subgraph",
                            {"entities": entities, "relations": relations},
                            endpoint=self.endpoint,
                        )
                    )
            # spatio-temporal retrieval
            plan = (
                state.data.get("plan", {})
                if isinstance(state.data.get("plan"), dict)
                else {}
            )
            bbox = state.data.get("bbox") or plan.get("bbox")
            time_range = state.data.get("time_range") or plan.get("time_range")
            if (
                isinstance(bbox, list)
                and len(bbox) == 4
                and isinstance(time_range, dict)
                and {"valid_from", "valid_to"} <= set(time_range)
            ):
                results = self._spatial_query(
                    [float(x) for x in bbox],
                    float(time_range["valid_from"]),
                    float(time_range["valid_to"]),
                )
                if results:
                    state.data["spatial_context"] = results
            snapshot = state.data.get("snapshot") or plan.get("snapshot")
            if isinstance(snapshot, dict) and {"valid_at", "tx_at"} <= set(snapshot):
                results = self._snapshot_query(
                    float(snapshot["valid_at"]),
                    float(snapshot["tx_at"]),
                )
                if results:
                    state.data["snapshot_context"] = results
            if "skill_query_vector" in state.data:
                results = self._query_skill_vector(state.data["skill_query_vector"])
                if results:
                    state.data["skill_results"] = results
            if "skill_query_metadata" in state.data:
                query = state.data["skill_query_metadata"]
                if isinstance(query, dict):
                    results = self._query_skill_metadata(query)
                    if results:
                        state.data.setdefault("skill_results", []).extend(results)
        except Exception:  # pragma: no cover - log only
            logger.exception("Failed to consolidate memory")
        return state
