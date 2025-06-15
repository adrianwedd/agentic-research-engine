from __future__ import annotations

import random
import time
from typing import Callable, Dict, List

Record = Dict[str, float | int | bool]


def generate_data(n: int = 200, seed: int = 42) -> List[Record]:
    """Create synthetic memory records with timestamps, relevance, and usage flag."""
    random.seed(seed)
    now = 1000
    data: List[Record] = []
    for i in range(n):
        timestamp = now - random.randint(0, 1000)
        relevance = random.random()
        used = random.random() < 0.2
        data.append(
            {"id": i, "timestamp": timestamp, "relevance": relevance, "used": used}
        )
    return data


def recency_prune(records: List[Record], max_age: int = 300) -> List[Record]:
    cutoff = max(r["timestamp"] for r in records) - max_age
    return [r for r in records if r["timestamp"] >= cutoff]


def relevance_prune(records: List[Record], threshold: float = 0.5) -> List[Record]:
    return [r for r in records if r["relevance"] >= threshold]


def hybrid_prune(
    records: List[Record], max_age: int = 300, threshold: float = 0.5
) -> List[Record]:
    cutoff = max(r["timestamp"] for r in records) - max_age
    return [
        r for r in records if r["relevance"] >= threshold or r["timestamp"] >= cutoff
    ]


def evaluate(records: List[Record], strategy: Callable[[List[Record]], List[Record]]):
    start = time.perf_counter()
    pruned = strategy(records)
    latency = time.perf_counter() - start
    total_used = sum(1 for r in records if r["used"])
    kept_used = sum(1 for r in pruned if r["used"])
    recall = kept_used / total_used if total_used else 1.0
    return len(pruned), latency, recall


if __name__ == "__main__":
    records = generate_data()
    strategies = {
        "recency": lambda rs: recency_prune(rs, max_age=300),
        "relevance": lambda rs: relevance_prune(rs, threshold=0.5),
        "hybrid": lambda rs: hybrid_prune(rs, max_age=300, threshold=0.5),
    }
    total = len(records)
    for name, strat in strategies.items():
        size, latency, recall = evaluate(records, strat)
        print(
            f"{name}: remaining {size}/{total} items, latency={latency*1000:.2f}ms, recall={recall:.2f}"
        )
