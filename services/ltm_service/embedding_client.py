from __future__ import annotations

"""Embedding client interfaces for Episodic Memory."""

import hashlib
from functools import lru_cache
from typing import Callable, List


class EmbeddingError(Exception):
    """Raised when the embedding service fails."""


class EmbeddingClient:
    """Abstract embedding API client."""

    def embed(
        self, texts: List[str]
    ) -> List[List[float]]:  # pragma: no cover - interface
        raise NotImplementedError


class SimpleEmbeddingClient(EmbeddingClient):
    """Deterministic embedding based on SHA1 hashing for tests."""

    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha1(text.encode()).digest()
            # Map first 5 bytes to floats in [0, 1]
            vectors.append([b / 255.0 for b in digest[:5]])
        return vectors


class CachedEmbeddingClient(EmbeddingClient):
    """LRU-cached wrapper around another embedding client."""

    def __init__(self, base_client: EmbeddingClient, cache_size: int = 512) -> None:
        self.base = base_client
        self.cache_size = cache_size

        @lru_cache(maxsize=cache_size)
        def _embed_single(text: str) -> tuple[float, ...]:
            return tuple(self.base.embed([text])[0])

        self._embed_single: Callable[[str], tuple[float, ...]] = _embed_single

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [list(self._embed_single(text)) for text in texts]
