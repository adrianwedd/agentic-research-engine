# ADR-002: Scheduled LTM Forgetting Job

To keep episodic memory healthy and performant, stale records must be pruned on a regular basis. The production deployment now includes a Kubernetes `CronJob` that executes `scripts/episodic_forgetting_job.py` every night at **02:00 UTC**. The job deletes episodes not accessed in the last 180 days.

The schedule and TTL are configurable via Helm values:

```yaml
forgetting:
  enabled: true
  schedule: "0 2 * * *"
  ttlDays: "180"
```

The CronJob calls the LTM service's HTTP API. It fetches episodic memories via
`/memory` and deletes stale ones with the `/forget` endpoint. The service URL is
configured via the `LTM_BASE_URL` environment variable and defaults to the
`agent-services` service. The CronJob times out after five minutes and retries
once if it fails, ensuring transient database issues do not leave stale data
behind. Job output is captured in the cluster logs so operations can audit how
many records were pruned each run. A metric `ltm.deletions` is emitted for
monitoring.
