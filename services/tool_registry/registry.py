from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Dict
from urllib.parse import parse_qs, urlparse

import yaml


class AccessDeniedError(Exception):
    """Raised when an agent lacks permission for a tool."""


class ToolRegistry:
    """Central registry mapping tools to agent permissions."""

    def __init__(self, permissions_path: str | None = None) -> None:
        self._tools: Dict[str, Callable] = {}
        self.permissions: Dict[str, list[str]] = {}
        if permissions_path:
            self.load_permissions(permissions_path)

    def load_permissions(self, path: str) -> None:
        data = yaml.safe_load(open(path)) or {}
        self.permissions = data.get("permissions", {})

    def register_tool(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def get_tool(self, agent_role: str, tool_name: str) -> Callable:
        allowed = self.permissions.get(agent_role, [])
        if tool_name not in allowed:
            raise AccessDeniedError(f"{agent_role} cannot access {tool_name}")
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Tool not found: {tool_name}") from exc


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
            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path != "/tool":
                    self.send_response(404)
                    self.end_headers()
                    return
                params = parse_qs(parsed.query)
                role = params.get("agent", [""])[0]
                name = params.get("name", [""])[0]
                try:
                    registry.get_tool(role, name)
                except AccessDeniedError as e:
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
