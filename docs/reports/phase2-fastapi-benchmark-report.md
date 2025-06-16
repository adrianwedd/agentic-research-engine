# FastAPI Benchmark Report

Recent load testing evaluated the async FastAPI implementation of the LTM service. The legacy `HTTPServer` version sustained roughly **20 RPS** before P95 latency exceeded 300 ms.

The FastAPI service was exercised with Locust at 20–160 concurrent users. Peak throughput of **321 RPS** was observed with 20 users while maintaining sub‑100 ms P95 latency. Even at 40 users the service delivered about **169 RPS** with P95 around 320 ms.

The results in `benchmarks/performance/fastapi_benchmarks.json` confirm a >10× throughput increase over the HTTPServer baseline while memory and CPU utilization remained moderate.
