from __future__ import annotations

"""Simple skill library for storing reusable policies with embeddings."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .episodic_memory import InMemoryStorage, StorageBackend
from .vector_store import InMemoryVectorStore, VectorStore


@dataclass
class Skill:
    """Container for a single skill."""

    policy: Any
    embedding: List[float]
    metadata: Dict[str, Any]


class SkillLibrary:
    """Store and retrieve skills with vector search support."""

    def __init__(
        self,
        storage_backend: StorageBackend | None = None,
        *,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.storage = storage_backend or InMemoryStorage()
        self.vector_store = vector_store or InMemoryVectorStore()

    def add(self, skill: Skill, skill_id: Optional[str] = None) -> str:
        record = {
            "skill": {
                "policy": skill.policy,
                "embedding": skill.embedding,
                "metadata": skill.metadata,
            }
        }
        if skill_id:
            record["id"] = skill_id
        sid = self.storage.save(record)
        self.vector_store.add(skill.embedding, {"id": sid})
        return sid

    def get(self, skill_id: str) -> Skill | None:
        rec = self.storage._data.get(skill_id)
        if not rec or rec.get("deleted_at"):
            return None
        data = rec.get("skill", {})
        if not data:
            return None
        return Skill(
            policy=data.get("policy"),
            embedding=list(data.get("embedding", [])),
            metadata=dict(data.get("metadata", {})),
        )

    def query(self, embedding: List[float], *, limit: int = 5) -> List[Skill]:
        results = self.vector_store.query(embedding, limit)
        skills: List[Skill] = []
        for rec in results:
            sk = self.get(rec["id"])
            if sk:
                skills.append(sk)
        return skills

    def search_metadata(self, key: str, value: Any) -> List[Skill]:
        skills = []
        for sid, rec in self.storage._data.items():
            if rec.get("deleted_at"):
                continue
            meta = rec.get("skill", {}).get("metadata", {})
            if meta.get(key) == value:
                sk = self.get(sid)
                if sk:
                    skills.append(sk)
        return skills
