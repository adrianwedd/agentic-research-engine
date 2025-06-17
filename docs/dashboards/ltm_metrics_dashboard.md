# LTM Metrics Dashboard

The monitoring service exports counters for each long-term memory module. These metrics help operators understand recall effectiveness and data quality.

## Metrics

- `ltm.hits` – number of successful retrievals
- `ltm.misses` – number of failed retrievals

Both metrics include a `memory_type` attribute with values `episodic`, `semantic`, and `procedural`. Dashboards group these counters to visualize hit rates over time.

