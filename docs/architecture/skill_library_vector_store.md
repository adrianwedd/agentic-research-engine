# SkillLibrary Vector Store Deployment

The SkillLibrary uses a Weaviate instance to persist skill embeddings and metadata.
Terraform configuration is provided under `infra/skill_library_vector_db` to deploy this database via the Helm chart.

## Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `storage_size` | Persistent volume size allocated to the database | `10Gi` |
| `api_key` | Optional API key used to secure the Weaviate API | empty |

After applying the Terraform module, the service is reachable at
`skilllib-vector-db.<namespace>.svc.cluster.local:8080`.
Configure `WEAVIATE_URL` and `WEAVIATE_API_KEY` in the SkillLibrary service
to point to this endpoint.
