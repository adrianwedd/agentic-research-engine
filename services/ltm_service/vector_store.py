from __future__ import annotations

"""Persistent vector store implementations for episodic memory."""

import concurrent.futures
import os
import uuid
from typing import Dict, Iterable, List

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

    def delete(self, vec_id: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class WeaviateVectorStore(VectorStore):
    """Persistent vector store backed by a local Weaviate instance."""

    def __init__(
        self,
        *,
        persistence_path: str | None = None,
        workers: int | None = None,
    ) -> None:
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
        self._pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=workers or int(os.getenv("VECTOR_STORE_WORKERS", "4"))
        )

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
        if hasattr(self, "_pool"):
            self._pool.shutdown(wait=True)

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        meta = metadata.copy()
        meta.pop("id", None)
        self._collection.data.insert(properties=meta, vector=vector, uuid=vec_id)
        return vec_id

    def _query_sync(self, vector: List[float], limit: int = 5) -> List[Dict]:
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

    def query(self, vector: List[float], limit: int = 5) -> List[Dict]:
        if getattr(self, "_pool", None):
            return self._pool.submit(self._query_sync, vector, limit).result()
        return self._query_sync(vector, limit)

    def query_many(
        self, vectors: Iterable[List[float]], *, limit: int = 5
    ) -> List[List[Dict]]:
        if not vectors:
            return []
        if getattr(self, "_pool", None):
            futures = [self._pool.submit(self._query_sync, v, limit) for v in vectors]
            return [f.result() for f in futures]
        return [self._query_sync(v, limit) for v in vectors]

    def delete(self, vec_id: str) -> None:
        try:
            self._collection.data.delete(uuid=vec_id)
        except Exception:  # pragma: no cover - best effort cleanup
            pass
