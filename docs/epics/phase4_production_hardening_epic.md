# Epic: Phase 4 - Production Hardening and Specialization

This epic translates the updated Phase 4 blueprint into a structured set of change requests. It focuses on expanding procedural memory, agent specialization, mandatory citation handling, and production resilience.

## Objectives
- Implement procedural memory to store and reuse successful skills.
- Fine-tune specialized agents and route tasks based on expertise.
- Enforce citation generation for all final reports.
- Harden the system with observability and fault recovery mechanisms.

## Change Requests

1. **P4-01R – Procedural Memory Framework**
   - Expand `LTMService` with a `ProceduralMemoryService` and expose matching endpoints.
   - Provide contract tests verifying storage and execution of procedures.
2. **P4-02R – Agent Instrumentation for Skill Logging**
   - Record sequences of tool calls and send successful traces to procedural memory.
   - Capture tool usage via tracing spans for debugging.
3. **P4-03R – Procedure Execution Path**
   - Allow agents to query procedural memory before planning and execute matching skills.
   - Add fallback logic when no procedure matches.
4. **P4-04R – Observability: LTM Metrics**
   - Add counters for episodic, semantic, and procedural memory hits/misses.
   - Metrics `ltm.hits` and `ltm.misses` are exported with a `memory_type` label.
   - Expose these metrics via the monitoring service and update dashboards.
5. **P4-05R – Procedural Memory Recall Research**
   - Compared retrieval-augmented generation with fine-tuning for skill recall.
   - Findings favor a hybrid approach: use RAG to collect procedures and periodically fine-tune agents.
   - Results are documented in `docs/research` and reflected in the updated blueprint.
6. **P4-06R – Fine-Tuning Pipeline**
   - Implement the multi-agent fine-tuning pipeline using existing trainers as references.
   - Ensure jobs run in parallel on agent-specific datasets.
7. **P4-07R – Specialist Agent Selection**
   - Modify the Supervisor to select specialized agents based on skill metadata.
8. **P4-08R – Specialization Metrics**
   - Measure divergence between policy weights or embeddings after fine-tuning.
   - Integrate results into the evaluation report.
9. **P4-09R – CitationAgent Implementation**
   - Develop CitationAgent to match claims with supporting passages and format citations (APA/MLA).
   - Enforce CitationAgent as a final workflow node.
10. **P4-10R – Production Hardening**
    - Add state checkpointing after every node execution for resumability.
    - Implement exponential backoff across tool wrappers and expand MAST tests.
11. **P4-11R – Security Enhancements**
    - Integrate automated `pip-audit` scans into CI and sanitize all file/URL inputs.
    - Document secrets-management procedures in the README.
12. **P4-12R – Address Outstanding Phase 3 Gaps**
    - Implement hierarchical subgraph state propagation, persistent semantic memory, improved relation extraction, and concurrency stress tests.

## Next Steps
Each change request should be logged in the change request ledger and broken down into tasks within `codex_tasks.md`. Implementation should track progress against earlier audits to ensure production readiness.
## Audit Status
The Phase 4 implementation audit recorded the following progress:

| Change Request | Status |
| --- | --- |
| P4-01R – Procedural Memory Framework | ✔ Implemented |
| P4-02R – Agent Instrumentation for Skill Logging | ✔ Implemented |
| P4-03R – Procedure Execution Path | ✔ Implemented |
| P4-04R – Observability: LTM Metrics | ✔ Implemented |
| P4-05R – Procedural Memory Recall Research | ✔ Implemented |
| P4-06R – Fine-Tuning Pipeline | ✔ Implemented |
| P4-07R – Specialist Agent Selection | ✗ Missing |
| P4-08R – Specialization Metrics | ✔ Implemented |
| P4-09R – CitationAgent Implementation | ✔ Implemented |
| P4-10R – Production Hardening | ✔ Implemented |
| P4-11R – Security Enhancements | ⚠ Partially implemented |
| P4-12R – Address Outstanding Phase 3 Gaps | ⚠ Partially implemented |

_Source: [Phase 4 Implementation Audit](../reports/p4_gap_analysis.md)._ 
