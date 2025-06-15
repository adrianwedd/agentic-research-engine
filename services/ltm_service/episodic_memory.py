"""Episodic memory module for storing and retrieving past task experiences."""

import json
import time
import uuid
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter

from .embedding_client import EmbeddingClient, EmbeddingError, SimpleEmbeddingClient
from .vector_store import InMemoryVectorStore, VectorStore, WeaviateVectorStore


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
        if self.vector_store:
            vector = self._embed_with_retry([query_text])[0]
            results = []
            for rec in self.vector_store.query(vector, limit):
                stored = dict(self.storage._data.get(rec["id"], {}))
                stored.update(rec)
                results.append(stored)
        else:
            results = []
            for _, rec in self.storage.all():
                context_text = json.dumps(rec.get("task_context", {}), sort_keys=True)
                score = self._similarity(query_text, context_text)
                rec = rec.copy()
                rec["similarity"] = score
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
