# Contributing Agents

This guide explains how to add custom agents to the system.

## Folder Structure

Agent implementations live under the `agents/` directory. Each agent folder must contain:

- `config.yml` – default configuration and tool definitions
- `prompt.tpl.md` – the Jinja template used to craft prompts

## Creating a Custom Agent

1. Create a new folder under `agents/` with your agent's name.
2. Add a `config.yml` file with any default settings and tool list.
3. Create a `prompt.tpl.md` file describing how the agent should respond.
4. Register the agent in your orchestration graph or configuration.

Example layout:

```text
agents/
└── MyAgent/
    ├── config.yml
    └── prompt.tpl.md
```

Minimal `config.yml` example:

```yaml
description: Demo agent
tools:
  - search
```

The `prompt.tpl.md` might contain:

```
You are MyAgent. Answer the question: {{ query }}
```

Build the documentation with:

```bash
mkdocs build
```

### ExampleAgent

This repository includes a minimal example agent in `agents/ExampleAgent/`:

```text
agents/
└── ExampleAgent/
    ├── config.yml
    └── prompt.tpl.md
```

`config.yml`:

```yaml
agent_name: "ExampleAgent"
role: "Minimal demonstration agent"
max_retries: 1
rbac: []
```

`prompt.tpl.md`:

```
You are ExampleAgent. Respond to the user query: {{ query }}
```

