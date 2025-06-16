# Consolidated Change Requests & Suggestions

This document aggregates improvement notes and change requests across reports and research documents.

## Orchestration

- **Unify State Representation** – consolidate duplicate dataclasses in `agents/supervisor.py` to use `engine.state.State`【F:docs/reports/phase2-architecture-health-report.md†L50-L58】 (priority: low)
- **Typed Edge Support** – extend the orchestration engine `add_edge` API to accept metadata such as labels【F:docs/reports/phase2-architecture-health-report.md†L59-L62】 (priority: low)
- **Enforce Tool Registry Use** – route all tool calls through `services.tool_registry` for RBAC compliance【F:docs/reports/phase2-architecture-health-report.md†L63-L66】 (priority: low)
- **Harden Evaluation Pipeline** – add contract tests and CI hooks for the judge pipeline【F:docs/reports/phase2-architecture-health-report.md†L67-L70】 (priority: low)
- **Fix State Propagation from Hierarchical Subgraphs** – ensure subgraph results propagate to parent graphs and add tests【F:docs/reports/p3_gap_analysis.md†L34-L40】 (priority: low)
- **Implement Concurrency Stress Tests** – simulate simultaneous scratchpad writes to verify locking behavior【F:docs/reports/p3_gap_analysis.md†L41-L44】 (priority: low)

## Memory

- **Cache Frequently Used Embeddings** – add an LRU cache in `EmbeddingClient` to avoid duplicate work【F:docs/reports/phase2-performance-bottlenecks-report.md†L14-L20】 (priority: low)
- **Switch to Async HTTP Framework** – replace `HTTPServer` with `FastAPI`/`uvicorn` for parallel requests【F:docs/reports/phase2-performance-bottlenecks-report.md†L14-L22】 (priority: low)
- **Parallelize Vector Store Operations** – use a worker pool for similarity search to scale on multi-core hosts【F:docs/reports/phase2-performance-bottlenecks-report.md†L14-L23】 (priority: low)
- **Enforce `memory_type` Parameter Validation** – validate and authorize memory operations in LTM API【F:docs/reports/phase2-ltm-api-gap-report.md†L18-L25】 (priority: low)
- **Add Contract Tests for LTM API** – extend `tests/test_ltm_service_api.py` with schema checks【F:docs/reports/phase2-ltm-api-gap-report.md†L26-L31】 (priority: low)
- **Document LTM OpenAPI Spec** – provide a versioned spec for LTM endpoints【F:docs/reports/phase2-ltm-api-gap-report.md†L32-L36】 (priority: low)
- **Extend `/retrieve` Query Flexibility** – support filtering by `memory_type` and keywords【F:docs/reports/phase2-ltm-api-gap-report.md†L34-L37】 (priority: low)
- **Schedule Periodic Forgetting Job** – integrate `scripts/episodic_forgetting_job.py` for pruning stale memories【F:docs/reports/p2_gap_analysis.md†L44-L48】 (priority: low)
- **Align Semantic LTM with Graph DB Spec** – replace in-memory store with Neo4j or document alternate approach【F:docs/reports/p3_gap_analysis.md†L38-L40】 (priority: low)
- **Improve MemoryManager Relation Extraction** – enhance `_extract_triples` for complex relationships and add tests【F:docs/reports/p3_gap_analysis.md†L41-L43】 (priority: low)

## API & Security

- **Rename Verb-Based Routes** – adopt snake_case nouns for consistency (e.g., `/memory/consolidate`)【F:docs/reports/phase2-api-consistency-report.md†L40-L45】 (priority: low)
- **Standardize Error Responses** – always return JSON `{ "error": msg }` with appropriate codes【F:docs/reports/phase2-api-consistency-report.md†L40-L47】 (priority: low)
- **Avoid JSON Bodies on GET** – move search parameters to query string for `/retrieve`【F:docs/reports/phase2-api-consistency-report.md†L40-L48】 (priority: low)
- **Validate Supervisor Plan Schema** – enforce schema on plan ingestion【F:docs/reports/phase2-api-consistency-report.md†L40-L50】 (priority: low)
- **Integrate Automated Dependency Scanning** – run `pip-audit` or similar in CI【F:docs/reports/phase2-security-audit-report.md†L40-L46】 (priority: high)
- **Validate File and URL Inputs** – whitelist URL schemes and sanitize paths in tools【F:docs/reports/phase2-security-audit-report.md†L47-L49】 (priority: medium)
- **Document Secrets Management** – recommend secret manager usage over environment variables【F:docs/reports/phase2-security-audit-report.md†L50-L52】 (priority: medium)
- **Expand RBAC Logging** – record failed authorization attempts in Tool Registry Server【F:docs/reports/phase2-security-audit-report.md†L53-L54】 (priority: low)
- **Monitor Third-Party Updates** – schedule monthly dependency updates and audits【F:docs/reports/phase2-security-audit-report.md†L55-L56】 (priority: low)

## Developer Experience

- **Improve Onboarding Guide** – document common setup issues and provide an env setup script【F:docs/reports/phase2-devex-review-report.md†L34-L37】 (priority: high)
- **Add Tracing Spans for Tool Initialization** – cover tool wrappers for end-to-end tracing【F:docs/reports/phase2-devex-review-report.md†L38-L40】 (priority: medium)
- **Clarify CI Output** – summarize failing checks and link to coverage artifacts【F:docs/reports/phase2-devex-review-report.md†L41-L43】 (priority: medium)
- **Trim Optional Tests** – allow a lightweight test subset for faster iteration【F:docs/reports/phase2-devex-review-report.md†L44-L45】 (priority: low)

## Testing & Tooling

- **Enforce Branch Protection** – block direct pushes to `main` and require CI checks before merge【F:docs/reports/phase1-gap-analysis-report.md†L35-L39】 (priority: low)
- **Enforce Coverage Threshold in CI** – require ≥80% coverage in the workflow【F:docs/reports/phase1-gap-analysis-report.md†L39-L42】【F:docs/reports/phase1-uat-gap-analysis-report.md†L44-L49】 (priority: low)
- **Expand Tracing of State Transitions** – instrument orchestration edges following `tracing_schema.md`【F:docs/reports/phase1-gap-analysis-report.md†L42-L44】 (priority: low)
- **Validate Supervisor Plan Output** – add strict schema validation for YAML plans【F:docs/reports/phase1-gap-analysis-report.md†L44-L46】 (priority: low)
- **Harden PDF Reader Wrapper** – improve OCR fallback and error handling【F:docs/reports/phase1-gap-analysis-report.md†L46-L48】 (priority: low)
- **Enhance Integration Harness** – add timeout configurability and partial failure handling【F:docs/reports/phase1-gap-analysis-report.md†L48-L50】 (priority: low)
- **Document Branch Protection Rules** – describe required settings in contributing guide【F:docs/reports/phase1-revalidation-gap-analysis.md†L36-L38】 (priority: low)
- **Align CD Pipeline with Rainbow Deployment** – update scripts or document rationale【F:docs/reports/phase1-revalidation-gap-analysis.md†L38-L40】 (priority: low)
- **Improve HTML Scraper Reliability** – evaluate `trafilatura` or headless browser approach【F:docs/reports/phase1-revalidation-gap-analysis.md†L40-L42】 (priority: low)

## Miscellaneous Research Suggestions

- **Filter LLM-Generated Skills** – use verification or evolutionary search to refine LLM-suggested subgoals【F:docs/research/2025-procedural-memory-skill-generalization.md†L74-L89】 (priority: low)
- **Dynamic Auction Mechanism Selection** – choose auction type adaptively based on task value and budget【F:docs/research/2025-computational-economy-for-multi-agents.md†L70-L75】 (priority: low)

