# Performance Enhancements

The Episodic Memory service uses an in-memory LRU cache to avoid generating embeddings for identical text chunks multiple times. The cache size is controlled via the `EMBED_CACHE_SIZE` environment variable.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBED_CACHE_SIZE` | Maximum number of distinct text chunks to cache for embeddings. Set to `0` to disable caching. | `0` |

A larger cache improves retrieval latency at the cost of additional memory. With a cache size of 512 entries, we observed roughly a 15% reduction in P95 retrieval latency in the local benchmark.

