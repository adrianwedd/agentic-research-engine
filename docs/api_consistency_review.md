# API Consistency Review

This document catalogs the current HTTP APIs and evaluates them against common design conventions.

## Public Endpoints

| Service | Method & Path | Payload | Success Status | Error Format |
|---------|---------------|---------|----------------|--------------|
| LTM Service | `POST /consolidate` | `{memory_type, record}` JSON body | `201` | `{"error": msg}` |
| LTM Service | `GET /retrieve` | JSON body `{query}` with query params `memory_type`, `limit` | `200` | `{"error": msg}` |
| Tool Registry | `GET /tool` | Query params `agent`, `name` | `200` | `{"error": msg}` on 403/404 |
| HITL Review | `GET /tasks` | none | `200` | empty body on 404 |
| HITL Review | `POST /tasks/<id>/approve` | none | `200` | `{"error": "not found"}` |
| HITL Review | `POST /tasks/<id>/reject` | none | `200` | `{"error": "not found"}` |

## Naming & Structure

* Endpoints mix verbs (`/consolidate`, `/retrieve`, `/approve`) and nouns (`/tasks`, `/tool`).
* Query parameters use `snake_case` (`memory_type`, `limit`), but paths do not use underscores except in verbs.
* Error responses generally use an `{ "error": "..." }` envelope but the status codes vary (`400`, `403`, `404`).
* Success codes differ (`201` vs `200`).
* The Supervisor planning schema requires the top-level fields `query`, `context`, `graph.nodes`, `graph.edges`, and `evaluation.metric`.

## Scorecard

* **Endpoints reviewed:** 6
* **Consistent naming:** 3/6 (50%) – mixed verb/noun usage
* **Consistent payload structure:** 4/6 (67%) – LTM endpoints differ (body vs query params)
* **Consistent error format:** 4/6 (67%) – HITL `GET /tasks` lacks JSON envelope
* **Overall consistency:** ~61%

## Notable Deviations

1. **Verb vs noun paths** – `/consolidate` and `/retrieve` use verbs while `/tool` and `/tasks` use nouns. A single style should be chosen.
2. **Error envelopes** – `HITLReview` `GET /tasks` returns an empty body on unknown path whereas other endpoints return `{"error": msg}`.
3. **Status codes** – `POST /consolidate` returns `201` while other successful calls return `200`.
4. **Payload placement** – `GET /retrieve` expects a JSON body, which is uncommon for `GET` requests.

## Change Requests

1. **CR-API-01:** Rename verb-based routes to snake_case nouns, e.g. `POST /memory/consolidate` and `GET /memory/retrieve` or `POST /consolidate_memory`.
2. **CR-API-02:** Standardize error responses to always return JSON `{"error": msg}` with appropriate status codes.
3. **CR-API-03:** Modify `GET /retrieve` to accept search parameters via the query string only, avoiding JSON bodies on GET.
4. **CR-API-04:** Ensure Supervisor plans are validated against `docs/supervisor_plan_schema.yaml` on ingestion.

Consistency improvements based on these CRs would bring the API surface closer to a unified style.
