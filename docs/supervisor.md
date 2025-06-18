# Supervisor Agent

This document describes how to configure the Supervisor agent.

## Plan templating

The Supervisor automatically reuses past plans retrieved from the episodic LTM service.
Retrieved memories are scored against the current query and the highest scoring plan
structure is merged into the generated plan. This results in similar intents producing
similar plan skeletons.

### Enabling

Plan templating is enabled by default. Set the environment variable `USE_PLAN_TEMPLATES=0`
or pass `use_plan_templates=False` to disable the behavior.
The number of memories considered is controlled by `retrieval_limit`.

## Specialist agent selection

Pass `available_agents` and `agent_skills` to `SupervisorAgent` to route tasks to
the most relevant specialist. `agent_skills` maps each agent id to a list of
skill tags. The Supervisor scores each task topic against these tags and assigns
the agent with the highest overlap.

