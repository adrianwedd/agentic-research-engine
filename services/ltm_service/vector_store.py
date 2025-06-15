from __future__ import annotations

"""In-memory vector store for episodic memory tests."""

import math
import uuid
from typing import Dict, Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    import weaviate
    from weaviate.embedded import EmbeddedOptions
except Exception:  # pragma: no cover - optional dependency missing
    weaviate = None


class VectorStore:
    """Minimal vector storage interface."""

    def add(
        self, vector: List[float], metadata: Dict
    ) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def query(
        self, vector: List[float], limit: int
    ) -> List[Dict]:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector storage with cosine similarity search."""

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[List[float], Dict]] = {}

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        self._data[vec_id] = (vector, metadata)
        return vec_id

    def query(self, vector: List[float], limit: int = 5) -> List[Dict]:
        def cosine(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

        scored = []
        for vec_id, (vec, meta) in self._data.items():
            score = cosine(vector, vec)
            rec = dict(meta)
            rec.setdefault("id", vec_id)
            rec["similarity"] = score
            scored.append((score, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored[:limit]]

    def all(self) -> Iterable[Tuple[str, Dict]]:
        for vec_id, (vec, meta) in self._data.items():
            rec = dict(meta)
            rec.setdefault("id", vec_id)
            yield vec_id, {"vector": vec, **rec}


class WeaviateVectorStore(VectorStore):
    """Persistent vector store backed by a local Weaviate instance."""

    def __init__(self, *, persistence_path: str | None = None) -> None:
        if weaviate is None:  # pragma: no cover - dependency missing
            raise RuntimeError("weaviate-client not installed")

        options = EmbeddedOptions(
            persistence_data_path=persistence_path or "/tmp/weaviate-data",
            binary_path="/tmp/weaviate-bin",
            additional_env_vars={
                "ENABLE_MODULES": "",
                "DISABLE_TELEMETRY": "true",
                "DEFAULT_VECTORIZER_MODULE": "none",
            },
        )
        self._client = weaviate.connect_to_embedded(options=options)

        if "Memory" not in self._client.collections.list():
            self._client.collections.create(
                name="Memory",
                vectorizer_config=weaviate.config.Configure.vectorizer.none(),
            )
        self._collection = self._client.collection("Memory")

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        meta = metadata.copy()
        meta.pop("id", None)
        self._collection.data.insert(properties=meta, vector=vector, uuid=vec_id)
        return vec_id

    def query(self, vector: List[float], limit: int = 5) -> List[Dict]:
        results = (
            self._collection.query.near_vector(vector)
            .with_additional(["distance"])
            .with_limit(limit)
            .do()
        )
        records = []
        for obj in results.objects:
            meta = obj.properties or {}
            meta.setdefault("id", obj.uuid)
            meta["similarity"] = 1.0 - obj.distance
            records.append(meta)
        records.sort(key=lambda r: r["similarity"], reverse=True)
        return records
