from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional


class SemanticMemoryService:
    """Simple in-memory semantic memory for storing triples."""

    def __init__(self) -> None:
        self._facts: List[Dict[str, Any]] = []

    def store_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        fact_id = str(uuid.uuid4())
        self._facts.append(
            {
                "id": fact_id,
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "properties": properties or {},
            }
        )
        return fact_id

    def query_facts(
        self,
        *,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for fact in self._facts:
            if fact.get("deleted_at"):
                continue
            if subject and fact["subject"] != subject:
                continue
            if predicate and fact["predicate"] != predicate:
                continue
            if object and fact["object"] != object:
                continue
            results.append(fact)
        return results

    def forget_fact(self, fact_id: str, *, hard: bool = False) -> bool:
        for fact in list(self._facts):
            if fact["id"] != fact_id:
                continue
            if hard:
                self._facts.remove(fact)
            else:
                fact["deleted_at"] = time.time()
            return True
        return False
