from __future__ import annotations

"""In-memory vector store for episodic memory tests."""

import math
import os
import uuid
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    import weaviate
    from weaviate.embedded import EmbeddedOptions
except Exception:  # pragma: no cover - optional dependency missing
    weaviate = None

try:  # pragma: no cover - optional dependency
    from milvus_lite.server import Server as MilvusLiteServer
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        connections,
        utility,
    )
except Exception:  # pragma: no cover - optional dependency missing
    MilvusLiteServer = None  # type: ignore


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


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector storage with cosine similarity search."""

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[List[float], Dict]] = {}

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        self._data[vec_id] = (vector, metadata)
        return vec_id

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    @staticmethod
    def _score_item(args: Tuple[List[float], Tuple[str, Tuple[List[float], Dict]]]):
        vector, item = args
        vec_id, (vec, meta) = item
        score = InMemoryVectorStore._cosine(vector, vec)
        rec = dict(meta)
        rec.setdefault("id", vec_id)
        rec["similarity"] = score
        return score, rec

    def query(self, vector: List[float], limit: int = 5) -> List[Dict]:
        scored = []
        items = list(self._data.items())
        workers = int(os.getenv("VECTOR_SEARCH_WORKERS", "1") or 1)
        if workers > 1 and items:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                scored = list(
                    ex.map(self._score_item, [(vector, item) for item in items])
                )
        else:
            for item in items:
                scored.append(self._score_item((vector, item)))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored[:limit]]

    def all(self) -> Iterable[Tuple[str, Dict]]:
        for vec_id, (vec, meta) in self._data.items():
            rec = dict(meta)
            rec.setdefault("id", vec_id)
            yield vec_id, {"vector": vec, **rec}

    def delete(self, vec_id: str) -> None:
        self._data.pop(vec_id, None)


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

    def delete(self, vec_id: str) -> None:
        try:
            self._collection.data.delete(uuid=vec_id)
        except Exception:  # pragma: no cover - best effort cleanup
            pass


class MilvusVectorStore(VectorStore):
    """Persistent vector store backed by a local Milvus Lite instance."""

    def __init__(self, *, persistence_path: str | None = None, dim: int = 768) -> None:
        if MilvusLiteServer is None:  # pragma: no cover - dependency missing
            raise RuntimeError("pymilvus not installed")

        db_file = os.path.join(persistence_path or "/tmp", "milvus.db")
        self._server = MilvusLiteServer(db_file)
        self._server.init()
        self._server.start()
        connections.connect(alias="default", uri=self._server.uds_path)
        self._dim = dim

        if utility.has_collection("Memory"):
            self._collection = Collection("Memory")
        else:
            fields = [
                FieldSchema(
                    "id",
                    DataType.VARCHAR,
                    is_primary=True,
                    auto_id=False,
                    max_length=64,
                ),
                FieldSchema("vector", DataType.FLOAT_VECTOR, dim=dim),
                FieldSchema("meta", DataType.JSON),
            ]
            schema = CollectionSchema(fields)
            self._collection = Collection("Memory", schema)
            self._collection.create_index(
                "vector", {"metric_type": "L2", "index_type": "FLAT"}
            )

    def close(self) -> None:
        try:
            connections.disconnect("default")
        except Exception:
            pass
        if self._server:
            self._server.stop()
            self._server = None

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        meta = metadata.copy()
        meta.pop("id", None)
        self._collection.insert([[vec_id], [vector], [meta]])
        self._collection.flush()
        return vec_id

    def query(self, vector: List[float], limit: int = 5) -> List[Dict]:
        results = self._collection.search(
            [vector],
            "vector",
            output_fields=["meta"],
            param={"metric_type": "L2"},
            limit=limit,
        )[0]
        records = []
        for hit in results:
            meta = hit.entity.get("meta", {})
            meta.setdefault("id", hit.id)
            meta["similarity"] = 1.0 - hit.distance
            records.append(meta)
        records.sort(key=lambda r: r["similarity"], reverse=True)
        return records

    def delete(self, vec_id: str) -> None:
        try:
            self._collection.delete(f"id == '{vec_id}'")
        except Exception:  # pragma: no cover - best effort cleanup
            pass
