# Performance Enhancements

The Episodic Memory service uses an in-memory LRU cache to avoid generating embeddings for identical text chunks multiple times. The cache size is controlled via the `EMBED_CACHE_SIZE` environment variable.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBED_CACHE_SIZE` | Maximum number of distinct text chunks to cache for embeddings. Set to `0` to disable caching. | `0` |
| `VECTOR_SEARCH_WORKERS` | Number of worker processes to use for similarity search in the in-memory vector store. Set to `1` for serial execution. | `1` |

A larger cache improves retrieval latency at the cost of additional memory. With a cache size of 512 entries, we observed roughly a 15% reduction in P95 retrieval latency in the local benchmark.

Parallel vector search can further improve throughput on multi-core hosts. Adjust `VECTOR_SEARCH_WORKERS` based on available CPU cores. On an 8‑core machine, using 4 workers yielded around a 30% increase in requests per second compared to the single-worker baseline.


## FastAPI Migration
The legacy `HTTPServer` implementation was replaced with FastAPI for asynchronous request handling.
Key entry points include `services/episodic_memory/app.py` and `services/ltm_service/openapi_app.py` where the FastAPI apps are defined.

## Deployment Configuration
Set the `WORKER_COUNT` environment variable to control the number of Uvicorn worker processes.
For local development you can start the service with:

```bash
uvicorn services.episodic_memory.app:app --host 0.0.0.0 --port 8081 --workers ${WORKER_COUNT:-4}
```

The Dockerfile and Helm chart also honor this variable for container deployments.

## Benchmark Results
Load testing results are summarized in `docs/fastapi_benchmark_report.md`.
Switching to FastAPI achieved over a 10× throughput increase versus the previous HTTP server while keeping latency under 100 ms at moderate concurrency.
