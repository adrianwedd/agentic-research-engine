# Supervisor Agent

This document describes how to configure the Supervisor agent.

## Plan templating

The Supervisor can reuse past plans retrieved from the episodic LTM service. When
`USE_PLAN_TEMPLATES` is enabled, retrieved memories are scored against the current
query and the highest scoring plan structure is merged into the generated plan.
This results in similar intents producing similar plan skeletons.

### Enabling

Set the environment variable `USE_PLAN_TEMPLATES=1` or pass
`use_plan_templates=True` to `SupervisorAgent` when constructing it.
The number of memories considered is controlled by `retrieval_limit`.

## Specialist agent selection

Pass `available_agents` and `agent_skills` to `SupervisorAgent` to route tasks to
the most relevant specialist. `agent_skills` maps each agent id to a list of
skill tags. The Supervisor scores each task topic against these tags and assigns
the agent with the highest overlap.

