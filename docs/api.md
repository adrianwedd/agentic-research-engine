# LTM Service API

The Long-Term Memory (LTM) service exposes an OpenAPI specification to help developers integrate with the service. The versioned schema is stored at [`docs/api/ltm_openapi.yaml`](docs/api/ltm_openapi.yaml) and is generated from [`services/ltm_service/openapi_app.py`](../services/ltm_service/openapi_app.py).

## Viewing the documentation

Run the FastAPI app and navigate to `http://localhost:8081/docs` to access the interactive Swagger UI. The raw specification is available at `http://localhost:8081/docs/openapi.json`.

## Regenerating the spec

After modifying the API, run the following command from the repository root to regenerate `docs/api/ltm_openapi.yaml`:

```bash
python -m services.ltm_service.generate_spec
```

This will output the current OpenAPI schema to `docs/api/ltm_openapi.yaml` so it can be committed to version control.
