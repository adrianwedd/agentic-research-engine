"""Procedural memory module built on top of episodic memory semantics."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

from .episodic_memory import EpisodicMemoryService


class ProceduralMemoryService(EpisodicMemoryService):
    """Store and execute reusable procedures."""

    def __init__(
        self,
        storage_backend,
        *,
        embedding_client=None,
        vector_store=None,
        action_registry: Dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        super().__init__(
            storage_backend,
            embedding_client=embedding_client,
            vector_store=vector_store,
        )
        self.action_registry: Dict[str, Callable[..., Any]] = action_registry or {
            "add": lambda a, b: a + b,
            "mul": lambda a, b: a * b,
        }

    def store_procedure(
        self, task_context: Dict, procedure: Iterable[Dict], outcome: Dict
    ) -> str:
        """Persist a procedure for later reuse."""
        return super().store_experience(
            task_context,
            {"procedure": list(procedure)},
            outcome,
        )

    def retrieve_similar_procedures(self, query: Dict, *, limit: int = 5) -> List[Dict]:
        """Retrieve procedures relevant to the query."""
        return super().retrieve_similar_experiences(query, limit=limit)

    def forget_procedure(self, procedure_id: str, *, hard: bool = False) -> bool:
        """Forget a stored procedure."""
        return super().forget_experience(procedure_id, hard=hard)

    def execute_procedure(self, procedure_id: str) -> List[Any]:
        """Execute the stored procedure and return step results."""
        rec = self.storage._data.get(procedure_id)
        if not rec or rec.get("deleted_at"):
            raise KeyError("procedure not found")
        steps = rec.get("execution_trace", {}).get("procedure", [])
        results = []
        for step in steps:
            action = step.get("action")
            func = self.action_registry.get(action)
            if func is None:
                raise ValueError(f"Unknown action: {action}")
            args = step.get("args", [])
            kwargs = step.get("kwargs", {})
            results.append(func(*args, **kwargs))
        return results
