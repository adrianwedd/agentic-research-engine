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

