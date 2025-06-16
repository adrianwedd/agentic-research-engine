# Blue-Green vs. Rainbow Deployment for Stateful Agents

The project blueprint specifies a **rainbow** deployment strategy to guarantee zero-downtime when rolling out new agent service versions. In practice, the `scripts/deploy.sh` helper currently performs a simpler **blue–green** switch over.

## Why Blue-Green?

- **Simpler namespace management.** Each color corresponds to a full deployment with its own label selector. Ephemeral agent pods can continue running under the old color until drained.
- **Reduced resource footprint.** Only two versions ever run at once, avoiding the proliferation of multicolored replicas typical of a rainbow rollout.
- **Kubernetes readiness gates.** The script waits for the new color's deployment to become ready before traffic is shifted, ensuring ongoing tasks are not interrupted.

While rainbow deployments gradually shift traffic across multiple versions, the blue-green approach still satisfies the blueprint's core requirement: new pods come online before the old ones are terminated, preserving long-lived agent workflows.

## Risk Mitigation

- Agent state is stored externally (e.g., in Redis and the LTM service), so pod replacement does not wipe working memory.
- Rolling back is fast: `scripts/rollback.sh` flips the service selector back to the previous color.

## Decision

Technical leadership approved continuing with blue-green deployments as the default strategy. The analysis above is recorded here to document the rationale for deviating from the original rainbow specification.
