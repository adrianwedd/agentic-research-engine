# AI Assurance Plan

This document outlines the assurance activities used to demonstrate that the agentic-research-engine operates within defined safety and policy constraints. Evidence from implemented components is mapped to each activity and reviewed on a recurring basis.

## Assurance Activities and Evidence

| Activity | Evidence |
|---------|---------|
| **Input/Output Guardrails** | Guardrail orchestration service validates prompts and logs moderation decisions. Implementation in `GuardrailService` shows checks for prompt injection and PII【F:services/guardrail_orchestrator/service.py†L15-L35】. |
| **Policy Enforcement** | `SafeguardAgent` monitors agent communication and emits alerts for violations. Prompt template defines how violations are reported【F:agents/SafeguardAgent/prompt.tpl.md†L1-L8】 with configuration in `config.yml`【F:agents/SafeguardAgent/config.yml†L1-L4】. |
| **Ethical Constitution** | Repository root `constitution.yaml` enumerates principles and banned terms that drive policy checks【F:constitution.yaml†L1-L14】. |
| **Benchmarking** | Performance and forgetting benchmarks validate system behavior under load and memory pruning strategies. Example benchmark located at `benchmarks/ltm_pruning_benchmark.py`【F:benchmarks/ltm_pruning_benchmark.py†L1-L15】. |

All evidence references are version controlled to preserve traceability.

## Review Schedule

Assurance artifacts are reviewed quarterly by the AI Safety Council. Each session logs discussion topics, outcomes, and action items in [review_log.md](review_log.md). The first review occurs within one month of adopting this plan.
