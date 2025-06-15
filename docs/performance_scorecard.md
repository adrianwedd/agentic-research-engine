# Performance Scorecard (P2-Review-05)

This scorecard summarizes load test results for the in-memory LTM service running on a single container CPU.
Metrics were collected using Locust and psutil.

| Metric | Value |
|-------|------|
| Requests | 2398 |
| Failures | 9 |
| Requests/sec | 238.6 |
| P50 Latency (ms) | 16 |
| P95 Latency (ms) | 210 |
| Avg CPU (%) | 17.8 |
| Peak Memory (MB) | 67.2 |

See `benchmarks/performance/performance_results.json` for raw data.
