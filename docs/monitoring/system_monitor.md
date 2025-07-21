# System Monitoring

The `SystemMonitor` class exports metrics and traces using OpenTelemetry. These metrics allow operators to track agent performance and long‑term memory health across deployments.

## Metrics

The monitor records several key metrics:

| Metric | Type | Description |
|-------|------|-------------|
| `agent.task_completion_time` | histogram (seconds) | How long it takes an agent to finish a task |
| `agent.resource_consumption` | histogram | Relative resource usage per task |
| `agent.quality_score` | histogram | Quality score reported by evaluators |
| `agent.error_count` | counter | Number of errors produced during a task |
| `agent.collaboration_effectiveness` | histogram | Collaboration score between agents |
| `ltm.hits` | counter | Successful long‑term memory lookups |
| `ltm.misses` | counter | Failed long‑term memory lookups |
| `ltm.deletions` | counter | Records removed from long‑term memory |

These metrics are defined in [`services/monitoring/system_monitor.py`](../../services/monitoring/system_monitor.py) and are emitted with the `agent_id` attribute so they can be correlated with traces.

## Setup

To enable monitoring, create a `SystemMonitor` using the helper constructor:

```python
from services.monitoring.system_monitor import SystemMonitor

monitor = SystemMonitor.from_otlp(endpoint="http://otel-collector:4317")
```

Set the `ENVIRONMENT` and `SERVICE_VERSION` environment variables so telemetry data is tagged appropriately. When running the provided `docker-compose.yml`, the OpenTelemetry collector, Jaeger, and supporting services will start automatically:

```bash
ENVIRONMENT=dev SERVICE_VERSION=0.1.0 docker-compose up -d
```

## Example OTLP Collector Configuration

The repository ships with an example collector configuration at [`otel-collector-config.yaml`](../../otel-collector-config.yaml). It exposes both gRPC and HTTP receivers and forwards traces to Jaeger:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:
processors:
  memory_limiter:
    limit_mib: 400
    check_interval: 1s
  batch:
    send_batch_size: 1024
    timeout: 5s
  queued_retry:
    num_workers: 4
    queue_size: 10000
  attributes:
    actions:
      - key: environment
        value: ${ENVIRONMENT}
        action: upsert
      - key: service.version
        value: ${SERVICE_VERSION}
        action: upsert
exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
service:
  telemetry:
    metrics:
      address: 0.0.0.0:8888
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, queued_retry, attributes]
      exporters: [jaeger]
```

This configuration can be used as‑is or extended to forward data to another OTLP‑compatible backend.
