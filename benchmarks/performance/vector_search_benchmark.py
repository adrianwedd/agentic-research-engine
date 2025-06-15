from __future__ import annotations

import json
import os
import random
import time

from services.ltm_service.vector_store import InMemoryVectorStore


def benchmark(workers: int, store_size: int = 2000, queries: int = 500) -> float:
    random.seed(0)
    store = InMemoryVectorStore()
    for i in range(store_size):
        vec = [random.random() for _ in range(5)]
        store.add(vec, {"id": str(i)})
    qvecs = [[random.random() for _ in range(5)] for _ in range(queries)]
    os.environ["VECTOR_SEARCH_WORKERS"] = str(workers)
    start = time.perf_counter()
    for q in qvecs:
        store.query(q, limit=5)
    return queries / (time.perf_counter() - start)


def main() -> None:
    results = {}
    for workers in [1, 2, 4, 8]:
        rps = benchmark(workers)
        results[str(workers)] = rps
        print(f"{workers} workers: {rps:.2f} q/s")
    with open("benchmarks/performance/vector_search_benchmark.json", "w") as fh:
        json.dump(results, fh, indent=2)


if __name__ == "__main__":
    main()
