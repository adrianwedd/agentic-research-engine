from __future__ import annotations

"""Persistent vector store implementations for episodic memory.

The service now connects to an external Weaviate instance by default. If
``WEAVIATE_URL`` is not set, a local embedded instance is started for
development and tests. Authentication can be supplied via the
``WEAVIATE_API_KEY`` environment variable.
"""

import concurrent.futures
import os
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

    def delete(self, vec_id: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class SimpleVectorStore(VectorStore):
    """In-memory vector store used when Weaviate is unavailable."""

    def __init__(self) -> None:
        self._data: List[Tuple[str, List[float], Dict]] = []

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        self._data.append((vec_id, vector, metadata))
        return vec_id

    def query(self, vector: List[float], limit: int) -> List[Dict]:
        def similarity(v1: List[float], v2: List[float]) -> float:
            if not v1 or not v2:
                return 0.0
            score = sum(a * b for a, b in zip(v1, v2))
            return score / (len(v1) ** 0.5 * len(v2) ** 0.5)

        results = []
        for vec_id, vec, meta in self._data:
            results.append(
                {"id": vec_id, **meta, "similarity": similarity(vector, vec)}
            )
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:limit]

    def delete(self, vec_id: str) -> None:
        self._data = [r for r in self._data if r[0] != vec_id]


class WeaviateVectorStore(VectorStore):
    """Persistent vector store backed by Weaviate."""

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        persistence_path: str | None = None,
        workers: int | None = None,
    ) -> None:
        if weaviate is None:  # pragma: no cover - dependency missing
            raise RuntimeError("weaviate-client not installed")

        url = url or os.getenv("WEAVIATE_URL")
        api_key = api_key or os.getenv("WEAVIATE_API_KEY")

        self._pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=workers or int(os.getenv("VECTOR_STORE_WORKERS", "4"))
        )

        if url:
            auth = weaviate.AuthApiKey(api_key) if api_key else None
            try:
                self._client = weaviate.Client(url, auth_client_secret=auth)
            except Exception:  # pragma: no cover - connection issues
                self._fallback = SimpleVectorStore()
                return
        else:
            options = EmbeddedOptions(
                persistence_data_path=persistence_path or "/tmp/weaviate-data",
                binary_path="/tmp/weaviate-bin",
                additional_env_vars={
                    "ENABLE_MODULES": "",
                    "DISABLE_TELEMETRY": "true",
                    "DEFAULT_VECTORIZER_MODULE": "none",
                },
            )
            try:
                self._client = weaviate.connect_to_embedded(options=options)
            except Exception:  # pragma: no cover - fallback when API mismatch
                try:
                    self._client = weaviate.connect_to_embedded(
                        hostname=options.hostname,
                        port=options.port,
                        grpc_port=options.grpc_port,
                        persistence_data_path=options.persistence_data_path,
                        binary_path=options.binary_path,
                        environment_variables=options.additional_env_vars,
                        version=options.version,
                    )
                except Exception:
                    self._fallback = SimpleVectorStore()
                    return

        if hasattr(self, "_fallback"):
            self._collection = None
        else:
            if "Memory" not in self._client.collections.list():
                self._client.collections.create(
                    name="Memory",
                    vectorizer_config=weaviate.config.Configure.vectorizer.none(),
                )
            self._collection = self._client.collection("Memory")

    def close(self) -> None:
        if hasattr(self, "_fallback"):
            self._fallback = None
        elif self._client:
            self._client.close()
            self._client = None
        if hasattr(self, "_pool"):
            self._pool.shutdown(wait=True)

    def add(self, vector: List[float], metadata: Dict) -> str:
        if hasattr(self, "_fallback"):
            return self._fallback.add(vector, metadata)
        vec_id = metadata.get("id", str(uuid.uuid4()))
        meta = metadata.copy()
        meta.pop("id", None)
        self._collection.data.insert(properties=meta, vector=vector, uuid=vec_id)
        return vec_id

    def _query_sync(self, vector: List[float], limit: int = 5) -> List[Dict]:
        if hasattr(self, "_fallback"):
            return self._fallback.query(vector, limit)
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
        if hasattr(self, "_fallback"):
            return self._fallback.query(vector, limit)
        if getattr(self, "_pool", None):
            return self._pool.submit(self._query_sync, vector, limit).result()
        return self._query_sync(vector, limit)

    def query_many(
        self, vectors: Iterable[List[float]], *, limit: int = 5
    ) -> List[List[Dict]]:
        if hasattr(self, "_fallback"):
            return [self._fallback.query(v, limit) for v in vectors]
        if not vectors:
            return []
        if getattr(self, "_pool", None):
            futures = [self._pool.submit(self._query_sync, v, limit) for v in vectors]
            return [f.result() for f in futures]
        return [self._query_sync(v, limit) for v in vectors]

    def delete(self, vec_id: str) -> None:
        if hasattr(self, "_fallback"):
            self._fallback.delete(vec_id)
            return
        try:
            self._collection.data.delete(uuid=vec_id)
        except Exception:  # pragma: no cover - best effort cleanup
            pass
