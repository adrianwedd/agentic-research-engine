# Long-Term Memory Consolidation & Forgetting Research (P2-19A)

This document summarizes a research spike into lifecycle management algorithms for the Long-Term Memory (LTM) service. The goal was to compare advanced forgetting strategies and recommend an approach for Phase 2 implementation.

## Candidate Algorithms

### 1. Selective Consolidation (Quality/Novelty)
- Inspired by hippocampal replay and RL prioritized experience replay.
- Memories are scored by novelty or confidence and only high-salience events are stored.
- **Pros:** Efficient storage, good at filtering noise.
- **Cons:** Requires reliable novelty metrics and may miss subtle but important facts.

### 2. Hybrid Time-Decay + Relevance
- Each memory's weight decays over time but can be refreshed when reused.
- Combines recency heuristics (LRU style) with a relevance score so that rarely accessed yet important facts persist longer.
- **Pros:** Simple to implement and tunable for different workloads.
- **Cons:** Needs careful threshold tuning; aggressive decay can drop useful context.

### 3. Value-Driven Forgetting
- Retention is tied to future utility or reward (e.g. TD‑error or user feedback).
- Low-value experiences are pruned to focus on memories that drive task success.
- **Pros:** Aligns storage with agent goals and can improve performance under constraints.
- **Cons:** Depends on accurate value estimates and introduces computational overhead.

## Proof-of-Concept Benchmark

A small benchmark (`benchmarks/ltm_pruning_benchmark.py`) simulates 200 memory records with timestamps, relevance scores and usage flags. Three pruning strategies were evaluated:

```
$ python benchmarks/ltm_pruning_benchmark.py
recency: remaining 66/200 items, latency=0.03ms, recall=0.28
relevance: remaining 102/200 items, latency=0.01ms, recall=0.53
hybrid: remaining 135/200 items, latency=0.03ms, recall=0.66
```

- **recency** removes the oldest items beyond a fixed age threshold.
- **relevance** keeps records with relevance >= 0.5.
- **hybrid** retains items if they are recent or above the relevance threshold.

The hybrid approach preserved the most relevant memories (66% recall on the synthetic dataset) while still reducing storage by ~32%, suggesting a balanced trade‑off between footprint and recall.

## Recommendation

Based on the literature review and the benchmark results, a **hybrid time‑decay with relevance scoring** is recommended for the initial forgetting mechanism. This strategy is straightforward to implement in the existing LTM service and can later be augmented with value-driven signals as more task feedback becomes available.
