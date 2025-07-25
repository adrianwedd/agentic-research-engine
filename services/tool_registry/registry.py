from __future__ import annotations

import datetime
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from . import AccessDeniedError, ToolRegistry

logger = logging.getLogger(__name__)


class ToolRegistryServer:
    """Minimal HTTP interface for the tool registry."""

    def __init__(
        self, registry: ToolRegistry, host: str = "127.0.0.1", port: int = 8000
    ) -> None:
        self.registry = registry
        self.host = host
        self.port = port
        self.httpd = HTTPServer((host, port), self._handler())

    def _handler(self):
        registry = self.registry

        class Handler(BaseHTTPRequestHandler):
            def log_message(
                self, format: str, *args
            ) -> None:  # pragma: no cover - quiet
                return

            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path != "/tool":
                    self.send_response(404)
                    self.end_headers()
                    return
                params = parse_qs(parsed.query)
                role = params.get("agent", [""])[0]
                name = params.get("name", [""])[0]
                user = self.headers.get("X-User", "")
                try:
                    registry.get_tool(role, name)
                except AccessDeniedError as e:
                    logger.warning(
                        json.dumps(
                            {
                                "timestamp": datetime.datetime.now(
                                    datetime.UTC
                                ).isoformat(),
                                "role": role,
                                "tool": name,
                                "user": user,
                                "client_ip": self.client_address[0],
                                "path": self.path,
                                "error": str(e),
                            }
                        )
                    )
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return
                except KeyError as e:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"tool": name}).encode())

        return Handler

    def serve_forever(self) -> None:  # pragma: no cover - manual run
        self.httpd.serve_forever()
