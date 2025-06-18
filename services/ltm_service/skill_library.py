from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .embedding_client import EmbeddingClient, SimpleEmbeddingClient
from .vector_store import VectorStore, WeaviateVectorStore


@dataclass
class Skill:
    policy: Dict[str, Any]
    embedding: List[float]
    metadata: Dict[str, Any]


class SkillLibrary:
    """Store and retrieve skills with vector search and metadata filters."""

    def __init__(
        self,
        *,
        embedding_client: EmbeddingClient | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.embedding_client = embedding_client or SimpleEmbeddingClient()
        self.vector_store = vector_store or WeaviateVectorStore()
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._frozen: set[str] = set()

    def add_skill(
        self,
        skill_policy: Dict[str, Any],
        skill_representation: str | List[float],
        skill_metadata: Dict[str, Any] | None = None,
        *,
        skill_id: str | None = None,
        overwrite: bool = False,
    ) -> str:
        """Store a skill and return its id."""

        if isinstance(skill_representation, str):
            vector = self.embedding_client.embed([skill_representation])[0]
        else:
            vector = list(skill_representation)
        skill_id = skill_id or str(uuid.uuid4())
        if skill_id in self._skills:
            if skill_id in self._frozen:
                raise ValueError("cannot overwrite frozen skill")
            if not overwrite:
                raise ValueError("skill already exists")
        metadata = skill_metadata or {}
        self._skills[skill_id] = {
            "id": skill_id,
            "skill_policy": skill_policy,
            "skill_representation": skill_representation,
            "skill_metadata": metadata,
        }
        self.vector_store.add(vector, {"id": skill_id, **metadata})
        return skill_id

    def get_skill(self, skill_id: str) -> Dict[str, Any] | None:
        return self._skills.get(skill_id)

    def query_by_vector(
        self, representation: str | List[float], limit: int = 5
    ) -> List[Dict[str, Any]]:
        if isinstance(representation, str):
            vector = self.embedding_client.embed([representation])[0]
        else:
            vector = list(representation)
        results = []
        for rec in self.vector_store.query(vector, limit):
            skill = self._skills.get(rec["id"])
            if skill:
                results.append(skill)
        return results

    def query_by_metadata(
        self, metadata_filter: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for skill in self._skills.values():
            meta = skill.get("skill_metadata", {})
            if all(meta.get(k) == v for k, v in metadata_filter.items()):
                results.append(skill)
                if len(results) >= limit:
                    break
        return results

    def all_skills(self) -> Iterable[Dict[str, Any]]:
        return list(self._skills.values())

    # --------------------------------------------------------------
    # Skill management helpers
    # --------------------------------------------------------------
    def freeze_skill(self, skill_id: str) -> None:
        """Prevent ``skill_id`` from being modified."""

        if skill_id in self._skills:
            self._frozen.add(skill_id)

    def is_frozen(self, skill_id: str) -> bool:
        return skill_id in self._frozen

    def compose_skill(self, skill_ids: List[str], prompt: str) -> str:
        """Compose a new skill from ``skill_ids`` using a primitive prompt."""

        actions: List[Any] = []
        for sid in skill_ids:
            skill = self._skills.get(sid)
            if skill:
                actions.extend(skill["skill_policy"].get("actions", []))
        policy = {"actions": actions}
        metadata = {"prompt": prompt, "base_skills": skill_ids}
        return self.add_skill(policy, prompt, metadata)
