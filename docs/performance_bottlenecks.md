# Performance Bottlenecks & Capacity Limits

Initial load testing revealed the LTM service can sustain roughly 20 RPS before response latency degrades sharply. CPU usage averaged around 35% with a peak memory footprint near 60 MB during the test. Because the storage backend and vector store run in-process, throughput is bound by Python's GIL and the single-threaded HTTP server implementation.

## Observed Bottlenecks
- Single-threaded `HTTPServer` limits request concurrency.
- Embedding generation in `EpisodicMemoryService` is synchronous and blocks other requests.
- Vector store queries scale linearly with stored records.

## Capacity Limits
The current setup is suitable for small-scale experiments but will not scale to production workloads without parallelism. Beyond ~20 concurrent users, error rates rise and response times exceed 300 ms P95.

## Proposed Change Requests
1. **Cache frequently used embeddings** – Introduce an LRU cache in `EmbeddingClient` to avoid repeated embedding calls for identical chunks. *Estimated improvement: 15% latency reduction on retrieval.*
2. **Switch to an async HTTP framework** – Replace `HTTPServer` with `FastAPI`/`uvicorn` to handle concurrent requests without blocking. *Estimated improvement: >2× max RPS.*
3. **Parallelize vector store operations** – Use a worker pool for similarity search to take advantage of multiple CPU cores. *Estimated improvement: 25% higher throughput on multi-core hosts.*
