"""Episodic memory module for storing and retrieving past task experiences."""

import json
import uuid
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Tuple


class StorageBackend:
    """Minimal storage backend interface."""

    def save(self, record: Dict) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def all(self) -> Iterable[Tuple[str, Dict]]:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryStorage(StorageBackend):
    """Simple in-memory storage for testing and local runs."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict] = {}

    def save(self, record: Dict) -> str:
        record_id = record.get("id", str(uuid.uuid4()))
        record["id"] = record_id
        self._data[record_id] = record
        return record_id

    def all(self) -> Iterable[Tuple[str, Dict]]:
        return list(self._data.items())


class EpisodicMemoryService:
    def __init__(self, storage_backend: StorageBackend) -> None:
        """Initialize episodic memory with persistent storage."""

        self.storage = storage_backend
        self.performance_by_category: defaultdict[str, List[int]] = defaultdict(list)

    def store_experience(
        self, task_context: Dict, execution_trace: Dict, outcome: Dict
    ) -> str:
        """Store complete task experience for future reference."""

        experience = {
            "task_context": task_context,
            "execution_trace": execution_trace,
            "outcome": outcome,
        }
        categories = set(task_context.get("tags", []))
        cat = task_context.get("category")
        if cat:
            categories.add(cat)
        experience["categories"] = list(categories)
        exp_id = self.storage.save(experience)

        success = outcome.get("success")
        if success is not None:
            for c in categories:
                self.performance_by_category[c].append(1 if success else 0)

        return exp_id

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def retrieve_similar_experiences(
        self, current_task: Dict, limit: int = 5
    ) -> List[Dict]:
        """Find relevant past experiences for current task."""

        query_text = json.dumps(current_task, sort_keys=True)
        scored: List[Tuple[float, Dict]] = []
        for _, rec in self.storage.all():
            context_text = json.dumps(rec.get("task_context", {}), sort_keys=True)
            score = self._similarity(query_text, context_text)
            rec = rec.copy()
            rec["similarity"] = score
            success_rates = {
                c: (
                    sum(self.performance_by_category[c])
                    / len(self.performance_by_category[c])
                )
                for c in rec.get("categories", [])
                if self.performance_by_category[c]
            }
            rec["success_rate"] = success_rates
            rec["warnings"] = [c for c, r in success_rates.items() if r < 0.5]
            scored.append((score, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:limit]]
