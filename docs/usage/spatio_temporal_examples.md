# Spatio-Temporal Examples

This guide demonstrates how research plans and the memory manager handle
queries with explicit time ranges or locations.

## Planning with Time and Location

When a user asks:

```
Wildfire reports in Europe from 2010 to 2020
```

the Supervisor includes temporal and spatial fields in the YAML plan:

```yaml
bbox: [-10.0, 35.0, 30.0, 60.0]
time_range:
  valid_from: 2010
  valid_to: 2020
```

## Memory Retrieval

The MemoryManager reads these parameters and issues a request to the LTM
service:

```
GET /spatial_query?bbox=-10.0,35.0,30.0,60.0&valid_from=2010&valid_to=2020
```

Results from the service are placed under `spatial_context` in the state
for downstream agents to use. A snapshot query can be specified with a
`snapshot` mapping containing `valid_at` and `tx_at` values.
