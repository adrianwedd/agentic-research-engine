from __future__ import annotations

"""Embedding client interfaces for Episodic Memory."""

import asyncio
import hashlib
import time
from functools import lru_cache
from typing import Callable, List, Dict, Optional, Tuple


class EmbeddingError(Exception):
    """Raised when the embedding service fails."""


class EmbeddingClient:
    """Abstract embedding API client."""

    def embed(
        self, texts: List[str]
    ) -> List[List[float]]:  # pragma: no cover - interface
        raise NotImplementedError


class SimpleEmbeddingClient(EmbeddingClient):
    """Optimized deterministic embedding based on SHA1 hashing for tests."""
    
    @lru_cache(maxsize=1024)
    def _embed_single_cached(self, text: str) -> Tuple[float, ...]:
        """Cache individual text embeddings."""
        digest = hashlib.sha1(text.encode()).digest()
        return tuple(b / 255.0 for b in digest[:5])

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding with caching."""
        return [list(self._embed_single_cached(text)) for text in texts]
        
    async def embed_async(self, texts: List[str]) -> List[List[float]]:
        """Async version for consistency."""
        return self.embed(texts)  # Already fast enough for sync


class CachedEmbeddingClient(EmbeddingClient):
    """High-performance LRU-cached wrapper with batch processing and TTL support."""

    def __init__(self, base_client: EmbeddingClient, cache_size: int = 2048, ttl_seconds: int = 3600) -> None:
        self.base = base_client
        self.cache_size = cache_size
        self.ttl_seconds = ttl_seconds
        self._cache_stats = {"hits": 0, "misses": 0}
        self._ttl_cache: Dict[str, Tuple[List[float], float]] = {}
        
        @lru_cache(maxsize=cache_size)
        def _embed_single_lru(text: str) -> tuple[float, ...]:
            return tuple(self.base.embed([text])[0])

        self._embed_single_lru: Callable[[str], tuple[float, ...]] = _embed_single_lru
    
    def _embed_single_with_ttl(self, text: str) -> List[float]:
        """Embed single text with TTL caching."""
        current_time = time.time()
        
        # Check TTL cache first
        if text in self._ttl_cache:
            embedding, timestamp = self._ttl_cache[text]
            if current_time - timestamp < self.ttl_seconds:
                self._cache_stats["hits"] += 1
                return embedding
            else:
                # Remove expired entry
                del self._ttl_cache[text]
        
        # Check LRU cache
        try:
            embedding_tuple = self._embed_single_lru(text)
            embedding = list(embedding_tuple)
            self._cache_stats["hits"] += 1
        except Exception:
            # Cache miss - compute embedding
            embedding = self.base.embed([text])[0]
            self._cache_stats["misses"] += 1
            
        # Store in TTL cache
        if len(self._ttl_cache) < self.cache_size:
            self._ttl_cache[text] = (embedding, current_time)
        
        return embedding

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Optimized batch embedding with intelligent caching."""
        if not texts:
            return []
            
        # For small batches, use individual caching
        if len(texts) <= 5:
            return [self._embed_single_with_ttl(text) for text in texts]
            
        # For larger batches, separate cached and uncached
        cached_results = {}
        uncached_texts = []
        uncached_indices = []
        
        current_time = time.time()
        
        for i, text in enumerate(texts):
            # Check TTL cache
            if text in self._ttl_cache:
                embedding, timestamp = self._ttl_cache[text]
                if current_time - timestamp < self.ttl_seconds:
                    cached_results[i] = embedding
                    self._cache_stats["hits"] += 1
                    continue
                else:
                    del self._ttl_cache[text]
                    
            # Check LRU cache
            try:
                embedding_tuple = self._embed_single_lru(text)
                cached_results[i] = list(embedding_tuple)
                self._cache_stats["hits"] += 1
            except Exception:
                uncached_texts.append(text)
                uncached_indices.append(i)
                self._cache_stats["misses"] += 1
        
        # Batch process uncached texts
        if uncached_texts:
            uncached_embeddings = self.base.embed(uncached_texts)
            for idx, embedding in zip(uncached_indices, uncached_embeddings):
                cached_results[idx] = embedding
                # Store in TTL cache if there's space
                if len(self._ttl_cache) < self.cache_size:
                    self._ttl_cache[texts[idx]] = (embedding, current_time)
        
        # Reconstruct results in original order
        return [cached_results[i] for i in range(len(texts))]
        
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache performance statistics."""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / total if total > 0 else 0.0
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": hit_rate,
            "lru_cache_size": self._embed_single_lru.cache_info().currsize if hasattr(self._embed_single_lru, 'cache_info') else 0,
            "ttl_cache_size": len(self._ttl_cache),
        }
        
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._embed_single_lru.cache_clear()
        self._ttl_cache.clear()
        self._cache_stats = {"hits": 0, "misses": 0}
        
    async def embed_async(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed for better integration."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed, texts)
