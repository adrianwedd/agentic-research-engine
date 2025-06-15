# Agent Action Tracing Schema

This document defines the standardized tracing schema used throughout the system.  All services and agents SHOULD emit spans that follow this schema so that traces are consistent and queryable.

## Versioning

The schema is versioned.  The current version is **1.0** and is exposed in the library `services.tracing.tracing_schema` via `SCHEMA_VERSION`.

## Tool Call Span

`ToolCallTrace` represents the primary span type for instrumenting tool usage.

### Attributes

| Attribute       | Description                          |
| --------------- | ------------------------------------ |
| `schema_version`| Tracing schema version identifier.   |
| `agent_id`      | Unique identifier of the agent.      |
| `agent_role`    | Role name of the agent.              |
| `tool_name`     | Name of the tool invoked.            |
| `tool_input`    | Input provided to the tool.          |
| `tool_output`   | Output returned from the tool.       |
| `input_tokens`  | Optional token count for the input.  |
| `output_tokens` | Optional token count for the output. |
| `latency_ms`    | Latency in milliseconds of the call. |

Agents are encouraged to populate token counts and latency whenever possible.
