# Integration Test Harness

This document describes how to run the BrowseComp integration tests and configure the harness.

## Running the Harness

Run the harness directly:

```bash
python tests/benchmarks/integration_harness.py
```

The harness will iterate over the dataset and report pass rates and timing statistics.

## Configuration

Several options can be configured via environment variables:

- `HARNESS_TIMEOUT` – per-question timeout in seconds (default `30`)
- `HARNESS_RETRIES` – number of retry attempts for each question on failure (default `0`)
- `HARNESS_RETRY_DELAY` – delay in seconds between retries (default `0.1`)

These variables allow the integration tests to handle flaky external calls and long-running tasks.
