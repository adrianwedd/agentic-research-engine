# Graph Compilation Strategies Research

This document summarizes a short research spike evaluating dynamic graph execution versus ahead-of-time (AOT) compilation for the orchestration engine.

## Proof-of-Concept Benchmark

A small benchmark was implemented in `benchmarks/graph_compilation.py`. It builds a simple five-node graph and measures runtime and memory usage for two approaches:

1. **Dynamic build** – a new graph is constructed and executed for every iteration.
2. **Compiled reuse** – a graph is compiled once and reused across iterations.

The benchmark was executed with 100 iterations using Python 3.12.
Re-running the script on a fresh container yielded faster times because the
sample graph is extremely small. Updated results:

```
Dynamic build+run: 0.0687s, peak 23189 bytes
Compiled run: 0.0604s, peak 10755 bytes
Hybrid run:   0.0631s, peak 11259 bytes
```

The compiled approach shows a small latency win and lower memory usage. The
hybrid test compiles a common subgraph while keeping the top level dynamic,
landing between the two extremes.

## Recommendation

A hybrid approach is advised:

- **Compile** well-defined subgraphs that run frequently or contain expensive logic.
- **Keep** the top-level orchestration dynamic so new tasks can modify graph structure at runtime.

This balances latency with flexibility and avoids unnecessary memory overhead for rarely used paths.
