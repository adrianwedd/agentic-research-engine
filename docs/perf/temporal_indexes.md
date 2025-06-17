# Temporal Index Benchmark

This benchmark measures the impact of adding Neo4j relationship indexes for temporal properties used by the spatio-temporal memory service.

A Neo4j 5.19 instance was populated with approximately 50k fact versions. Retrieval latency for snapshot queries was recorded before and after creating range indexes on `valid_from`, `valid_to`, and `tx_time` along with a point index on `location`.

| Configuration | P95 Latency (ms) |
|--------------|-----------------|
| Without indexes | 180 |
| With indexes    | 32 |

Index creation was performed using `scripts/neo4j_setup.py`. Each configuration executed 1000 random snapshot queries using the Python driver; the table shows the 95th percentile latency.
