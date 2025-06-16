"""Episodic memory module for storing and retrieving past task experiences."""

import json
import os
import time
import uuid
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except Exception:  # pragma: no cover - fallback

    class RecursiveCharacterTextSplitter:  # type: ignore
        """Fallback splitter that chunks text without dependencies."""

        def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 0) -> None:
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str) -> List[str]:
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size)
            ]


try:  # pragma: no cover - optional dependency
    from opentelemetry import trace
except Exception:  # pragma: no cover - fallback
    import contextlib

    class _DummyTracer:
        def get_tracer(self, *_, **__):  # type: ignore[override]
            class _Span:
                def start_as_current_span(self, *a, **kw):  # type: ignore[override]
                    return contextlib.nullcontext()

            return _Span()

    trace = _DummyTracer()  # type: ignore

from .embedding_client import (
    CachedEmbeddingClient,
    EmbeddingClient,
    EmbeddingError,
    SimpleEmbeddingClient,
)
from .vector_store import InMemoryVectorStore, VectorStore, WeaviateVectorStore


class StorageBackend:
    """Minimal storage backend interface."""

    def save(self, record: Dict) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def all(self) -> Iterable[Tuple[str, Dict]]:  # pragma: no cover - interface
        raise NotImplementedError

    def delete(self, record_id: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def update(
        self, record_id: str, updates: Dict
    ) -> None:  # pragma: no cover - interface
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

    def delete(self, record_id: str) -> None:
        self._data.pop(record_id, None)

    def update(self, record_id: str, updates: Dict) -> None:
        if record_id in self._data:
            self._data[record_id].update(updates)


class EpisodicMemoryService:
    def __init__(
        self,
        storage_backend: StorageBackend,
        *,
        embedding_client: EmbeddingClient | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        """Initialize episodic memory with persistent storage and vector search."""

        self.storage = storage_backend
        self.embedding_client = embedding_client or SimpleEmbeddingClient()

        cache_size = int(os.getenv("EMBED_CACHE_SIZE", "0") or 0)
        if cache_size > 0:
            self.embedding_client = CachedEmbeddingClient(
                self.embedding_client, cache_size
            )
        if vector_store is None:
            try:
                self.vector_store = WeaviateVectorStore()
            except Exception:
                self.vector_store = InMemoryVectorStore()
        else:
            self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=0
        )
        self.performance_by_category: defaultdict[str, List[int]] = defaultdict(list)

    def _embed_with_retry(
        self, texts: List[str], *, attempts: int = 3
    ) -> List[List[float]]:
        """Embed text with simple exponential backoff."""
        for i in range(attempts):
            try:
                return self.embedding_client.embed(texts)
            except Exception as exc:  # pragma: no cover - integration fallback
                if i == attempts - 1:
                    raise EmbeddingError(str(exc)) from exc
                time.sleep(2**i * 0.5)

    def store_experience(
        self, task_context: Dict, execution_trace: Dict, outcome: Dict
    ) -> str:
        """Store complete task experience for future reference."""

        now = time.time()
        experience = {
            "task_context": task_context,
            "execution_trace": execution_trace,
            "outcome": outcome,
            "last_accessed": now,
            "last_accessed_timestamp": now,
            "relevance_score": 1.0,
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

        # Generate embeddings and store in vector DB
        text = json.dumps(experience, sort_keys=True)
        chunks = self.text_splitter.split_text(text)
        vectors = self._embed_with_retry(chunks)
        for idx, vec in enumerate(vectors):
            metadata = {
                "id": exp_id,
                "chunk_index": idx,
                "text": chunks[idx],
                "categories": list(categories),
            }
            self.vector_store.add(vec, metadata)

        return exp_id

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def retrieve_similar_experiences(
        self, current_task: Dict, limit: int = 5
    ) -> List[Dict]:
        """Find relevant past experiences for current task."""
        query_text = json.dumps(current_task, sort_keys=True)

        # Prefer vector search if available
        boost = float(os.getenv("LTM_RELEVANCE_BOOST", "0.1"))
        if self.vector_store:
            vector = self._embed_with_retry([query_text])[0]
            results = []
            for rec in self.vector_store.query(vector, limit):
                stored = dict(self.storage._data.get(rec["id"], {}))
                if stored.get("deleted_at"):
                    continue
                stored.update(rec)
                self.storage.update(
                    rec["id"],
                    {
                        "last_accessed": time.time(),
                        "last_accessed_timestamp": time.time(),
                        "relevance_score": stored.get("relevance_score", 1.0) + boost,
                    },
                )
                results.append(stored)
        else:
            results = []
            for _, rec in self.storage.all():
                if rec.get("deleted_at"):
                    continue
                context_text = json.dumps(rec.get("task_context", {}), sort_keys=True)
                score = self._similarity(query_text, context_text)
                rec = rec.copy()
                rec["similarity"] = score
                if rec.get("id"):
                    self.storage.update(
                        rec["id"],
                        {
                            "last_accessed": time.time(),
                            "last_accessed_timestamp": time.time(),
                            "relevance_score": rec.get("relevance_score", 1.0) + boost,
                        },
                    )
                results.append(rec)

        for rec in results:
            categories = rec.get("categories", [])
            success_rates = {
                c: (
                    sum(self.performance_by_category[c])
                    / len(self.performance_by_category[c])
                )
                for c in categories
                if self.performance_by_category[c]
            }
            rec["success_rate"] = success_rates
            rec["warnings"] = [c for c, r in success_rates.items() if r < 0.5]

        # Vector store already sorts by similarity
        if not self.vector_store:
            results.sort(key=lambda r: r.get("similarity", 0), reverse=True)

        return results[:limit]

    def prune_stale_memories(self, ttl_seconds: float) -> int:
        """Delete memories not accessed within the TTL."""
        cutoff = time.time() - ttl_seconds
        pruned = 0
        tracer = trace.get_tracer(__name__)
        for rec_id, rec in list(self.storage.all()):
            last = rec.get("last_accessed", 0)
            if last < cutoff:
                self.storage.delete(rec_id)
                if hasattr(self.vector_store, "delete"):
                    try:
                        self.vector_store.delete(rec_id)
                    except Exception:  # pragma: no cover - best effort
                        pass
                pruned += 1
        with tracer.start_as_current_span(
            "ltm.prune", attributes={"pruned_count": pruned}
        ):
            pass
        return pruned

    def decay_relevance_scores(
        self,
        *,
        decay_rate: float = 0.99,
        threshold: float = 0.1,
    ) -> int:
        """Apply time-based decay and soft-delete stale memories."""
        now = time.time()
        pruned = 0
        for rec_id, rec in list(self.storage.all()):
            if rec.get("deleted_at"):
                continue
            last = rec.get("last_accessed_timestamp", rec.get("last_accessed", now))
            score = float(rec.get("relevance_score", 1.0))
            elapsed_days = (now - last) / 86400
            new_score = score * (decay_rate**elapsed_days)
            updates = {"relevance_score": new_score}
            if new_score < threshold:
                updates["deleted_at"] = now
                if hasattr(self.vector_store, "delete"):
                    try:
                        self.vector_store.delete(rec_id)
                    except Exception:
                        pass
                pruned += 1
            self.storage.update(rec_id, updates)
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "ltm.decay", attributes={"pruned_count": pruned}
        ):
            pass
        return pruned
