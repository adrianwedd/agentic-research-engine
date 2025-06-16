# ADR-002: Scheduled LTM Forgetting Job

To keep episodic memory healthy and performant, stale records must be pruned on a regular basis. The production deployment now includes a Kubernetes `CronJob` that executes `scripts/episodic_forgetting_job.py` every night at **02:00 UTC**. The job deletes episodes not accessed in the last 180 days.

The schedule and TTL are configurable via Helm values:

```yaml
forgetting:
  enabled: true
  schedule: "0 2 * * *"
  ttlDays: "180"
```

The CronJob times out after five minutes and retries once if it fails, ensuring transient database issues do not leave stale data behind. Job output is captured in the cluster logs so operations can audit how many records were pruned each run.
