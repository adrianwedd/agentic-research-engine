# Epic: P4-12R – Address Outstanding Phase 3 Gaps

Phase 3 introduced several features that were only partially implemented. The gap analysis highlights missing state propagation, a non-persistent semantic memory layer, limited relation extraction, and absent concurrency tests.

## Source Gap Analysis
- Hierarchical subgraph spawning lacks parent-child state return logic【F:docs/reports/p3_gap_analysis.md†L14-L14】.
- Semantic LTM deviates from the graph DB specification; it remains in-memory【F:docs/reports/p3_gap_analysis.md†L26-L26】.
- Relation extraction is only partially implemented with regex parsing【F:docs/reports/p3_gap_analysis.md†L27-L27】.
- No race-condition tests exist for concurrent scratchpad writes【F:docs/reports/p3_gap_analysis.md†L32-L32】.
- Follow-up change requests CR‑P3‑03A through CR‑P3‑21A expand on these issues【F:docs/reports/p3_gap_analysis.md†L34-L43】.

## Implementation Plan
1. **Hierarchical subgraph state propagation**
   - Update `OrchestrationEngine` so each subgraph merges its final state back into the parent before execution resumes.
   - Extend `Node.run` around the `SUBGRAPH` case to pass the merged scratchpad forward.
   - Add regression tests ensuring subgraphs modify parent state correctly.
2. **Persistent semantic memory via graph DB**
   - Replace the in-memory `SemanticMemoryService` with a Neo4j-backed implementation as outlined in the integration guide【F:docs/semantic_memory_neo4j.md†L1-L25】.
   - Configure `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` and fall back to in-memory mode in tests.
   - Extend integration tests to verify facts persist across process restarts.
3. **Improved relation extraction**
   - Enhance `MemoryManagerAgent._extract_triples` to parse nested or multiple relations.
   - Consider spaCy or a refined structured LLM prompt.
   - Provide unit tests covering complex sentences and edge cases.
4. **Concurrency stress tests**
   - Add optional locking in `engine/collaboration/group_chat.py` to prevent race conditions.
   - Create stress tests spawning many simultaneous writers to the scratchpad.
   - Validate final state consistency and no lost updates.
5. **Project hygiene**
   - Log tasks in `codex_tasks.md` and ensure `.codex/queue.yml` entries remain synchronized.
   - Document the Neo4j memory backend and concurrency testing approach under `docs/`.

## Expected Outcomes
- Parent graphs automatically receive updated state from completed subgraphs.
- Semantic facts persist in Neo4j, surviving service restarts.
- MemoryManager extracts richer triples from research outputs.
- Stress tests confirm scratchpad consistency under high concurrency.

## Audit Status
The Phase 4 audit marks this epic as ⚠ **Partially implemented**.
Underlying Phase 3 items remain unresolved:

- P3-03 Hierarchical subgraph spawning – ⚠ Partially implemented
- P3-15 Graph DB for Semantic LTM – ↔ Deviated
- P3-16 Entity/relation extraction – ⚠ Partially implemented
- P3-21 Race-condition QA tests – ✗ Missing

_Source: [Phase 4 Implementation Audit](../reports/p4_gap_analysis.md) and [Phase 3 Implementation Audit](../reports/p3_gap_analysis.md)._ 
