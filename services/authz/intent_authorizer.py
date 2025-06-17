from __future__ import annotations

"""Intent-based authorization middleware."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Iterable
from urllib.parse import urlparse

import yaml

from services.tool_registry import AccessDeniedError, ToolRegistry
from tools.validation import validate_path_or_url

logger = logging.getLogger(__name__)


class IntentAuthorizer:
    """Validate that a tool is allowed for a given intent."""

    def __init__(self, policy: Dict[str, Iterable[str]] | None = None) -> None:
        self.policy: Dict[str, set[str]] = {
            k: set(v) for k, v in (policy or {}).items()
        }

    @classmethod
    def from_yaml(cls, path: str) -> "IntentAuthorizer":
        sanitized = validate_path_or_url(path, allowed_schemes={"file"})
        data = yaml.safe_load(open(sanitized)) or {}
        return cls(data.get("intents", {}))

    def allowed(self, intent: str, tool: str) -> bool:
        allowed_tools = self.policy.get(intent, set())
        return tool in allowed_tools


class IntentAuthZServer:
    """HTTP sidecar enforcing intent-based authorization."""

    def __init__(
        self,
        registry: ToolRegistry,
        authorizer: IntentAuthorizer,
        *,
        host: str = "127.0.0.1",
        port: int = 8002,
    ) -> None:
        self.registry = registry
        self.authorizer = authorizer
        self.httpd = HTTPServer((host, port), self._handler())

    def _handler(self):
        registry = self.registry
        authorizer = self.authorizer

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:  # pragma: no cover
                return

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path != "/invoke":
                    self.send_response(404)
                    self.end_headers()
                    return
                length = int(self.headers.get("Content-Length", 0))
                data = self.rfile.read(length)
                try:
                    payload = json.loads(data) if data else {}
                except json.JSONDecodeError:
                    payload = {}
                role = payload.get("agent", "")
                intent = payload.get("intent", "")
                tool = payload.get("tool", "")
                args = payload.get("args", [])
                kwargs = payload.get("kwargs", {})

                if not authorizer.allowed(intent, tool):
                    logger.warning(
                        "ToolInvocationViolation(%s, %s, %s)", role, intent, tool
                    )
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "forbidden"}).encode())
                    return
                try:
                    result = registry.invoke(role, tool, *args, **kwargs)
                except AccessDeniedError as exc:
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(exc)}).encode())
                    return
                except KeyError as exc:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(exc)}).encode())
                    return

                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"result": result}).encode())

        return Handler

    def serve_forever(self) -> None:  # pragma: no cover - manual run
        self.httpd.serve_forever()
