# Agent Catalog

## 1. Overview
This document lists the core agents defined in the blueprint.

## 2. Directory Layout
Each agent has a folder under `agents/` containing a `config.yml` and `prompt.tpl.md`.

## 3. Core Agents

| Agent | Role | Trigger | Config Path |
|-----------------|---------------------------------------------------------|------------------------------------------|-------------------------------|
| Supervisor | High-level strategist: builds and synthesizes graph | On user query + post-verification | `agents/Supervisor/` |
| Planner | Optimization-based plan generator | After Supervisor LTM lookup | `agents/Planner/` |
| WebResearcher | Academic-grade web/internet researcher | On each research sub-task node | `agents/WebResearcher/` |
| CodeResearcher | Code analysis & sandbox execution | When `code_analysis_required` flag set | `agents/CodeResearcher/` |
| Evaluator | Fact-checker & self-correction loop manager | After each generation or synthesis step | `agents/Evaluator/` |
| MemoryManager | Episodic, semantic, procedural LTM operations | Post-delivery consolidation | `agents/MemoryManager/` |
| CitationAgent | Precise source-claim matching & citation insertion | CI post-test / final report | `agents/CitationAgent/` |
