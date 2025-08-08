from __future__ import annotations

"""Persistent vector store implementations for episodic memory.

<<<<<<< Updated upstream
The service now connects to an external Weaviate instance by default. If
``WEAVIATE_URL`` is not set, a local embedded instance is started for
development and tests. Authentication can be supplied via the
``WEAVIATE_API_KEY`` environment variable.
"""

import concurrent.futures
import os
import uuid
from typing import Dict, Iterable, List, Tuple
=======
import asyncio
import math
import os
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import lru_cache
from typing import Dict, Iterable, List, Tuple, Optional
>>>>>>> Stashed changes

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


<<<<<<< Updated upstream
class SimpleVectorStore(VectorStore):
    """In-memory vector store used when Weaviate is unavailable."""

    def __init__(self) -> None:
        self._data: List[Tuple[str, List[float], Dict]] = []
=======
class InMemoryVectorStore(VectorStore):
    """Optimized in-memory vector storage with parallel cosine similarity search."""

    def __init__(self, cache_size: int = 1000) -> None:
        self._data: Dict[str, Tuple[List[float], Dict]] = {}
        self._similarity_cache: Dict[str, float] = {}
        self._cache_size = cache_size
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        
    def _get_thread_pool(self) -> ThreadPoolExecutor:
        """Lazy initialization of thread pool for better resource management."""
        if self._thread_pool is None:
            workers = min(int(os.getenv("VECTOR_SEARCH_WORKERS", "4")), 8)
            self._thread_pool = ThreadPoolExecutor(max_workers=workers)
        return self._thread_pool
>>>>>>> Stashed changes

    def add(self, vector: List[float], metadata: Dict) -> str:
        vec_id = metadata.get("id", str(uuid.uuid4()))
        self._data.append((vec_id, vector, metadata))
        return vec_id

<<<<<<< Updated upstream
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
=======
    @staticmethod
    @lru_cache(maxsize=2048)
    def _cosine_cached(a_tuple: Tuple[float, ...], b_tuple: Tuple[float, ...]) -> float:
        """Cached cosine similarity with tuple inputs for hashability."""
        dot = sum(x * y for x, y in zip(a_tuple, b_tuple))
        norm_a = math.sqrt(sum(x * x for x in a_tuple))
        norm_b = math.sqrt(sum(x * x for x in b_tuple))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
    
    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        """Fast cosine similarity calculation."""
        return InMemoryVectorStore._cosine_cached(tuple(a), tuple(b))

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
        """Optimized query with parallel processing and caching."""
        items = list(self._data.items())
        if not items:
            return []
            
        # Use thread pool for I/O bound similarity calculations
        workers = min(int(os.getenv("VECTOR_SEARCH_WORKERS", "4")), len(items), 8)
        
        if workers > 1 and len(items) > 10:
            # Parallel processing for larger datasets
            executor = self._get_thread_pool()
            futures = []
            
            # Split work into batches for optimal performance
            batch_size = max(1, len(items) // workers)
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                future = executor.submit(self._score_batch, vector, batch)
                futures.append(future)
                
            scored = []
            for future in futures:
                scored.extend(future.result())
        else:
            # Sequential processing for small datasets
            scored = self._score_batch(vector, items)

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored[:limit]]
        
    def _score_batch(self, vector: List[float], items: List[Tuple[str, Tuple[List[float], Dict]]]) -> List[Tuple[float, Dict]]:
        """Score a batch of items for parallel processing."""
        scored = []
        for item in items:
            score_result = self._score_item((vector, item))
            scored.append(score_result)
        return scored
        
    async def query_async(self, vector: List[float], limit: int = 5) -> List[Dict]:
        """Async version of query for better integration with async codebases."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, vector, limit)

    def all(self) -> Iterable[Tuple[str, Dict]]:
        for vec_id, (vec, meta) in self._data.items():
            rec = dict(meta)
            rec.setdefault("id", vec_id)
            yield vec_id, {"vector": vec, **rec}

    def delete(self, vec_id: str) -> None:
        self._data.pop(vec_id, None)
        # Clear cache entries related to deleted vector
        self._similarity_cache = {k: v for k, v in self._similarity_cache.items() if vec_id not in k}
        
    def close(self) -> None:
        """Clean up resources."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
            
    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass  # Ignore cleanup errors during destruction


class WeaviateVectorStore(VectorStore):
    """Optimized persistent vector store with connection pooling and batch operations."""

    def __init__(self, *, persistence_path: str | None = None, pool_size: int = 5) -> None:
        if weaviate is None:  # pragma: no cover - dependency missing
            raise RuntimeError("weaviate-client not installed")

        self._pool_size = pool_size
        self._clients = []
        self._current_client_idx = 0
        
        # Initialize connection pool with optimized options
        options = EmbeddedOptions(
            persistence_data_path=persistence_path or "/tmp/weaviate-data",
            binary_path="/tmp/weaviate-bin",
            additional_env_vars={
                "ENABLE_MODULES": "",
                "DISABLE_TELEMETRY": "true",
                "DEFAULT_VECTORIZER_MODULE": "none",
                "QUERY_MAXIMUM_RESULTS": "10000",
                "QUERY_SLOW_LOG_ENABLED": "false",
            },
        )
        
        # Create primary client
        self._client = weaviate.connect_to_embedded(options=options)
        self._clients.append(self._client)
        
        # Initialize collection
        if "Memory" not in self._client.collections.list():
            self._client.collections.create(
                name="Memory",
                vectorizer_config=weaviate.config.Configure.vectorizer.none(),
            )
        self._collection = self._client.collection("Memory")
        
        # Create additional clients for connection pool (limited to avoid resource exhaustion)
        for _ in range(1, min(pool_size, 3)):
            try:
                client = weaviate.connect_to_embedded(options=options)
                self._clients.append(client)
            except Exception:
                break
>>>>>>> Stashed changes

    def _get_client(self):
        """Get next client from connection pool for load balancing."""
        if not self._clients:
            return self._client
        client = self._clients[self._current_client_idx]
        self._current_client_idx = (self._current_client_idx + 1) % len(self._clients)
        return client
        
    def close(self) -> None:
<<<<<<< Updated upstream
        if hasattr(self, "_fallback"):
            self._fallback = None
        elif self._client:
            self._client.close()
            self._client = None
        if hasattr(self, "_pool"):
            self._pool.shutdown(wait=True)
=======
        """Close all connections in the pool."""
        for client in self._clients:
            try:
                if client:
                    client.close()
            except Exception:
                pass
        self._clients.clear()
        self._client = None
>>>>>>> Stashed changes

    def add(self, vector: List[float], metadata: Dict) -> str:
        if hasattr(self, "_fallback"):
            return self._fallback.add(vector, metadata)
        vec_id = metadata.get("id", str(uuid.uuid4()))
        meta = metadata.copy()
        meta.pop("id", None)
        self._collection.data.insert(properties=meta, vector=vector, uuid=vec_id)
        return vec_id

<<<<<<< Updated upstream
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
=======
    def query(self, vector: List[float], limit: int = 5) -> List[Dict]:
        """Optimized query with connection pooling."""
        client = self._get_client()
        collection = client.collection("Memory")
        
        try:
            results = (
                collection.query.near_vector(vector)
                .with_additional(["distance"])
                .with_limit(min(limit, 100))  # Prevent excessive results
                .do()
            )
            
            records = []
            for obj in results.objects:
                meta = obj.properties or {}
                meta.setdefault("id", obj.uuid)
                meta["similarity"] = 1.0 - obj.distance
                records.append(meta)
            
            records.sort(key=lambda r: r["similarity"], reverse=True)
            return records[:limit]
        except Exception as e:
            # Fallback to primary client if pooled client fails
            if client != self._client:
                return self.query(vector, limit)
            raise e
            
    async def query_async(self, vector: List[float], limit: int = 5) -> List[Dict]:
        """Async version of query."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, vector, limit)
        
    def batch_add(self, vectors_and_metadata: List[Tuple[List[float], Dict]]) -> List[str]:
        """Batch insert for improved performance."""
        ids = []
        batch_size = 100  # Weaviate recommended batch size
        
        for i in range(0, len(vectors_and_metadata), batch_size):
            batch = vectors_and_metadata[i:i + batch_size]
            batch_ids = []
            
            with self._collection.batch.dynamic() as batch_client:
                for vector, metadata in batch:
                    vec_id = metadata.get("id", str(uuid.uuid4()))
                    meta = metadata.copy()
                    meta.pop("id", None)
                    
                    batch_client.add_object(
                        properties=meta,
                        vector=vector,
                        uuid=vec_id
                    )
                    batch_ids.append(vec_id)
                    
            ids.extend(batch_ids)
        return ids
>>>>>>> Stashed changes

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
