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

## `/skill`

```
POST /skill
```

Stores a skill in the library. The request body must include:

- `skill_policy` – policy representation (arbitrary JSON)
- `skill_representation` – text or vector used for embedding
- `skill_metadata` – arbitrary metadata dictionary

Returns the stored skill `id`.

## `/skill_vector_query`

```
POST /skill_vector_query
```

Retrieves skills similar to the provided vector or text query. Body fields:

- `query` – text or embedding vector
- `limit` – maximum number of results

The response contains a `results` list of skills.

## `/skill_metadata_query`

```
POST /skill_metadata_query
```

Retrieves skills whose metadata match the provided filter dictionary. Body fields:

- `query` – metadata filter dictionary
- `limit` – maximum number of results

The response contains a `results` list.
