# Phase 2 Architectural Conformance & Health Review

This document reviews the repository against the architectural blueprint in `BLUEPRINT.md`. It extracts the key patterns, maps implementation status, highlights deviations, and proposes follow‑up change requests.

## Core Architectural Patterns

The blueprint defines four foundational pillars:

1. **Hybrid Graph-Based Supervisor Model** – dynamic workflows executed as a stateful graph【F:BLUEPRINT.md†L8-L15】.
2. **Multi-Layered Long-Term Memory (LTM) Service** for episodic, semantic and procedural knowledge【F:BLUEPRINT.md†L8-L15】.
3. **Structured Self-Correction Loop** driven by an Evaluator agent【F:BLUEPRINT.md†L8-L15】.
4. **Multi-Faceted Evaluation Framework** including an LLM-as-a-Judge pipeline【F:BLUEPRINT.md†L8-L15】.

Additional CRs introduce:

- A central State object to pass information between nodes【F:BLUEPRINT.md†L310-L334】.
- A GroupChatManager enabling agent-to-agent collaboration【F:BLUEPRINT.md†L1233-L1255】.

## Component Mapping

| Component | Blueprint Pattern |
|-----------|------------------|
| `engine/orchestration_engine.py` | Hybrid Graph-Based Supervisor Model |
| `engine/state.py` | Central State object |
| `services/ltm_service/` | Multi-Layered LTM Service |
| `agents/evaluator.py` and `engine/routing.py` | Structured Self-Correction Loop |
| `pipelines/judge/` | LLM-as-a-Judge Evaluation Pipeline |
| `engine/collaboration/group_chat.py` | GroupChatManager for collaboration |
| `services/tool_registry/` | Secure Tool Registry supporting agents |

## Deviations and Anti‑Patterns

1. **Duplicate State Classes** – `agents/supervisor.py` defines its own `State` dataclass, diverging from the central `engine.state.State` and violating the single source of truth principle.
2. **Ad‑hoc Tool Calls** – some tools are invoked directly rather than via the Tool Registry, bypassing RBAC checks.
3. **Monolithic Engine Logic** – extending the orchestration engine (e.g., adding new edge metadata) requires touching multiple internal structures, indicating limited modularity.

## Modifiability Assessment

A small refactor attempted to add a typed edge (storing a label with each edge). This change required updating the edge list representation, the build order logic and several tests, revealing tight coupling between edge storage and routing. The engine is moderately modifiable but lacks clear extension points. **Rating:** 3/5.

## Scorecard

| Metric | Value |
|-------|------|
| Pattern Coverage | 5 / 6 (≈83%) |
| Anti-Pattern Count | 3 |
| Modifiability Rating | 3 / 5 |

## Proposed Change Requests

1. **CR-P3-01 – Unify State Representation**
   - **Rationale:** Remove duplicate dataclass in `agents/supervisor.py` and use `engine.state.State` everywhere. Ensures consistent serialization and auditing.
   - **Effort:** ~3 pts.
2. **CR-P3-02 – Typed Edge Support in Orchestration Engine**
   - **Rationale:** Extend `add_edge` to accept optional metadata (e.g., label or type). Improves flexibility for future routing features.
   - **Effort:** ~5 pts.
3. **CR-P3-03 – Enforce Tool Registry for All Tool Calls**
   - **Rationale:** Standardise access through `services.tool_registry` to guarantee RBAC and logging. Refactor direct imports in agents and tools.
   - **Effort:** ~3 pts.
4. **CR-P3-04 – Harden Evaluation Pipeline Integration**
   - **Rationale:** The LLM-as-a-Judge pipeline exists but lacks automated correlation tests and CI hooks. Add contract tests and pipeline triggers.
   - **Effort:** ~5 pts.

These CRs should enter the Phase 3 backlog to reduce architecture drift and improve maintainability.
