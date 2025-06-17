"""Procedural memory module built on top of episodic memory semantics."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Iterable, List

from .episodic_memory import EpisodicMemoryService, InMemoryStorage
from .skill_library import Skill, SkillLibrary


class ProceduralMemoryService(EpisodicMemoryService):
    """Store and execute reusable procedures."""

    def __init__(
        self,
        storage_backend,
        *,
        embedding_client=None,
        vector_store=None,
        action_registry: Dict[str, Callable[..., Any]] | None = None,
        skill_library: SkillLibrary | None = None,
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
        self.skill_library = skill_library or SkillLibrary(
            storage_backend=InMemoryStorage(),
            vector_store=self.vector_store,
        )
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    def store_procedure(
        self, task_context: Dict, procedure: Iterable[Dict], outcome: Dict
    ) -> str:
        """Persist a procedure for later reuse."""
        return super().store_experience(
            task_context,
            {"procedure": list(procedure)},
            outcome,
        )

    # --------------------------------------------------------------
    # Skill Library operations
    # --------------------------------------------------------------
    def store_skill(
        self,
        policy: Any,
        embedding: List[float],
        metadata: Dict[str, Any],
        *,
        skill_id: str | None = None,
    ) -> str:
        """Add a skill to the SkillLibrary."""

        skill = Skill(policy=policy, embedding=embedding, metadata=metadata)
        return self.skill_library.add(skill, skill_id)

    def retrieve_similar_skills(
        self, embedding: List[float], *, limit: int = 5
    ) -> List[Skill]:
        """Retrieve skills with embeddings similar to the query."""

        return self.skill_library.query(embedding, limit=limit)

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

    # --------------------------------------------------------------
    # Agent skill metadata helpers
    # --------------------------------------------------------------
    def register_agent(
        self,
        agent_id: str,
        *,
        domains: Iterable[str] | None = None,
        success_rate: float = 1.0,
    ) -> None:
        """Register or update metadata for an agent."""

        self.agent_metadata[agent_id] = {
            "domains": list(domains or []),
            "success_rate": float(success_rate),
        }
        self.logger.debug("Registered agent %s with domains=%s", agent_id, domains)

    def get_agent_metadata(self, agent_id: str) -> Dict[str, Any]:
        """Return stored metadata for the agent, if any."""

        return self.agent_metadata.get(agent_id, {})

    def all_agent_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Return metadata for all registered agents."""

        return self.agent_metadata
