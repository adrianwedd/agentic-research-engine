# Security Guide

This guide describes how to monitor RBAC failures in the Tool Registry.

## Viewing RBAC Logs

`ToolRegistryServer` logs every failed authorization attempt as a JSON record. Run the server normally and check its standard logs or your configured log aggregator.

Example log entry:

```json
{"timestamp": "2024-01-01T12:00:00Z", "role": "Supervisor", "tool": "dummy", "client_ip": "127.0.0.1", "path": "/tool?agent=Supervisor&name=dummy", "error": "Role 'Supervisor' cannot access tool 'dummy'"}
```

Fields:

- `timestamp` – UTC time of the request
- `role` – agent role making the request
- `tool` – requested tool name
- `client_ip` – IP address of the client
- `path` – HTTP path and query
- `error` – reason access was denied

Use `docker compose logs tool-registry` or your monitoring backend to search for these records and audit failed access attempts.
