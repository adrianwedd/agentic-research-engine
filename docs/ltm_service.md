# LTM Service RBAC

The LTM service exposes multiple HTTP endpoints. Access is controlled using the `X-Role` header. Requests are allowed only if the caller's role matches the endpoint requirements.

| Endpoint | Method | Allowed Roles |
|----------|-------|---------------|
| `/memory` | POST | `editor` |
| `/memory` | GET | `viewer`, `editor` |
| `/semantic_consolidate` | POST | `editor` |
| `/temporal_consolidate` | POST | `editor` |
| `/propagate_subgraph` | POST | `editor` |
| `/spatial_query` | GET | `viewer`, `editor` |
| `/skill` | POST | `editor` |
| `/skill_vector_query` | POST | `viewer`, `editor` |
| `/skill_metadata_query` | POST | `viewer`, `editor` |
| `/evaluator_memory` | POST | `editor` |
| `/evaluator_memory` | GET | `viewer`, `editor` |
| `/forget` | DELETE | `editor` |
| `/forget_evaluator` | DELETE | `editor` |
| `/provenance` | GET | `viewer`, `editor` |

If a request is made with an unauthorized role, the service returns `403 Forbidden`.
