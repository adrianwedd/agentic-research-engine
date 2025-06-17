# LTM Service HTTP API

This document describes the HTTP endpoints exposed by the Long-Term Memory service.

## `/spatial_query`

```
GET /spatial_query?bbox=<min_lon>,<min_lat>,<max_lon>,<max_lat>&valid_from=<ts>&valid_to=<ts>
```

Retrieves fact versions that were valid between `valid_from` and `valid_to` and whose location falls within the specified bounding box. The bounding box parameters are longitude/latitude pairs.

### Parameters
- `bbox` – comma-separated list `min_lon,min_lat,max_lon,max_lat`.
- `valid_from` – start of the time range (Unix timestamp).
- `valid_to` – end of the time range (Unix timestamp).

A successful response returns a JSON object with a `results` list containing matching facts.
