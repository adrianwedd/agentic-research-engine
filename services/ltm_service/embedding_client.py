from __future__ import annotations

"""Embedding client interfaces for Episodic Memory."""

import hashlib
from typing import List


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
