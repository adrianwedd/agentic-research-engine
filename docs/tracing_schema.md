# Agent Action Tracing Schema

This document defines the standardized tracing schema used throughout the system.  All services and agents SHOULD emit spans that follow this schema so that traces are consistent and queryable.

## Versioning

The schema is versioned.  The current version is **1.1** and is exposed in the library `services.tracing.tracing_schema` via `SCHEMA_VERSION`.
Earlier traces produced with version 1.0 remain readable via `ToolCallTrace.from_attributes`.

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

## Orchestration Spans

The orchestration engine records how state flows through the graph using a
number of additional span types.

### Node Span

Each node execution creates a span named `node:<name>`. Two attributes capture
the state before and after the node runs:

| Attribute     | Description                                  |
| ------------- | -------------------------------------------- |
| `state_in`    | JSON dump of the state at node entry         |
| `state_out`   | JSON dump of the state after the node exits  |

### Edge Span

Transitions between nodes are recorded with a span named `edge`.

| Attribute | Description                            |
| --------- | -------------------------------------- |
| `from`    | Name of the node where the edge starts |
| `to`      | Destination node name                  |

### Route Decision Span

When a router decides the next node, a `route` span is emitted.

| Attribute   | Description                                        |
| ----------- | -------------------------------------------------- |
| `node`      | Name of the router node                             |
| `decision`  | Raw routing result before any path mapping is done |

### Routing Span Example

The following JSON illustrates a router decision span:

```json
{
  "trace_id": "abc123",
  "span_id": "route1",
  "parent_span_id": "node5",
  "span.kind": "internal",
  "name": "route",
  "node_id": "router1",
  "decision": "fetch_data",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Edge spans generated after a routing decision share the same `trace_id` and use
the routing span's `span_id` as their `parent_span_id`. This linkage allows a
trace viewer to connect the decision to the subsequent transition between nodes.

### State Update Span

Mutations to the shared `State` object are traced with a `state.update` span.

| Attribute       | Description                                           |
| --------------- | ----------------------------------------------------- |
| `action`        | Either `update` or `add_message`                      |
| `keys`          | Comma separated list of keys updated (for `update`)   |
| `message_type`  | Included when the action is `add_message`             |
