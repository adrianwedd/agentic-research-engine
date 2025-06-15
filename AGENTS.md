# AGENTS Catalog & Guidelines

## Overview
This document consolidates the catalog of built-in agents and the contribution guidelines for this repository. It explains where agents live, how they are configured, and how to extend them.

## Directory Layout
Each agent resides in a folder under `agents/`. Every folder contains:
- `config.yml` – default settings for the agent
- `prompt.tpl.md` – the template used to generate prompts for the agent

## Core Agents
| Agent | Role | Trigger | Config Path |
|-----------------|---------------------------------------------------------|------------------------------------------|-------------------------------|
| Supervisor | High-level strategist: builds and synthesizes graph | On user query + post-verification | `agents/Supervisor/` |
| Planner | Optimization-based plan generator | After Supervisor LTM lookup | `agents/Planner/` |
| WebResearcher | Academic-grade web/internet researcher | On each research sub-task node | `agents/WebResearcher/` |
| CodeResearcher | Code analysis & sandbox execution | When `code_analysis_required` flag set | `agents/CodeResearcher/` |
| Evaluator | Fact-checker & self-correction loop manager | After each generation or synthesis step | `agents/Evaluator/` |
| MemoryManager | Episodic, semantic, procedural LTM operations | Post-delivery consolidation | `agents/MemoryManager/` |
| CitationAgent | Precise source-claim matching & citation insertion | CI post-test / final report | `agents/CitationAgent/` |

## Usage Guidance
- **Extending agents**: create a new folder under `agents/` with a `config.yml` and `prompt.tpl.md`. Use existing agents as references.
- **Configuring agents**: edit the YAML settings in each agent's `config.yml`. These define default tools and behavior. Customize prompts in `prompt.tpl.md` for specialized tasks.
- **Testing new agents**: after changes, run `bash scripts/agent-setup.sh` to install dependencies and hooks, then execute `pre-commit run --all-files` and `pytest -q`.
- **Best practices**: keep prompts short and focused, document any non-default settings in the README or within the agent directory, and ensure your configuration works with the existing evaluation suite.

## Code Style
- Use **Black** and **isort** for formatting Python code. Configure flake8 with max-line-length 120 and ignore E203. Run `pre-commit run --all-files` before committing.

## Testing
- Run tests with `pytest -q`.
- Execute `pre-commit run --all-files` to run linters and formatters.

## Setup
- Run `bash scripts/agent-setup.sh` to install Python dependencies and pre-commit hooks.

## PR Guidelines
- Summarize changes in the PR description.
- Include test results in the PR body.
- Ensure all tests and linters pass before opening a pull request.
