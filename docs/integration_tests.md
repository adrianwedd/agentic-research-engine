# Integration Test Harness

This document describes how to run the BrowseComp integration tests and configure the harness.

## Running the Harness

Run the harness directly:

```bash
python tests/benchmarks/integration_harness.py [--dataset path] [--timeout sec] [--retries n] [--retry-delay sec]
```

The harness will iterate over the dataset and report pass rates and timing statistics.

## Configuration

Several options can be configured via environment variables:

- `HARNESS_TIMEOUT` – per-question timeout in seconds (default `30`)
- `HARNESS_RETRIES` – number of retry attempts for each question on failure (default `0`)
- `HARNESS_RETRY_DELAY` – delay in seconds between retries (default `0.1`)

These variables allow the integration tests to handle flaky external calls and long-running tasks.

The same settings can be provided on the command line using the corresponding
`--timeout`, `--retries`, and `--retry-delay` flags. You may also specify an
alternative dataset with `--dataset` or `HARNESS_DATASET`.
