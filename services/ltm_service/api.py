from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Set, Tuple
from urllib.parse import parse_qs, urlparse

from .episodic_memory import EpisodicMemoryService

ALLOWED_MEMORY_TYPES: Set[str] = {"episodic", "semantic", "procedural"}

ROLE_PERMISSIONS: Dict[Tuple[str, str], Set[str]] = {
    ("POST", "/memory"): {"editor"},
    ("GET", "/memory"): {"viewer", "editor"},
    # Deprecated paths kept for one release cycle
    ("POST", "/consolidate"): {"editor"},
    ("GET", "/retrieve"): {"viewer", "editor"},
}


class LTMService:
    """Coordinate access to various memory modules."""

    def __init__(self, episodic_memory: EpisodicMemoryService) -> None:
        self._modules: Dict[str, EpisodicMemoryService] = {"episodic": episodic_memory}

    def consolidate(self, memory_type: str, record: Dict) -> str:
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        return module.store_experience(
            record.get("task_context", {}),
            record.get("execution_trace", {}),
            record.get("outcome", {}),
        )

    def retrieve(self, memory_type: str, query: Dict, *, limit: int = 5) -> List[Dict]:
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        return module.retrieve_similar_experiences(query, limit=limit)


class LTMServiceServer:
    """Minimal HTTP API for the LTM service."""

    def __init__(
        self, service: LTMService, host: str = "127.0.0.1", port: int = 8081
    ) -> None:
        self.service = service
        self.httpd = HTTPServer((host, port), self._handler())

    def _handler(self):
        service = self.service

        class Handler(BaseHTTPRequestHandler):
            def _json_body(self) -> Dict:
                length = int(self.headers.get("Content-Length", 0))
                if not length:
                    return {}
                data = self.rfile.read(length)
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return {}

            def _send_json(self, status: int, payload: Dict) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def _check_role(self, method: str, path: str) -> bool:
                role = self.headers.get("X-Role", "")
                allowed = ROLE_PERMISSIONS.get((method, path), set())
                return role in allowed

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path == "/consolidate":
                    # Temporary redirect to new noun-based endpoint
                    self.send_response(308)
                    self.send_header("Location", "/memory")
                    self.end_headers()
                    return
                if parsed.path != "/memory":
                    self.send_response(404)
                    self.end_headers()
                    return
                if not self._check_role("POST", "/memory"):
                    self._send_json(403, {"error": "forbidden"})
                    return
                data = self._json_body()
                record = data.get("record")
                memory_type = data.get("memory_type", "episodic")
                if record is None:
                    self._send_json(400, {"error": "missing record"})
                    return
                try:
                    rec_id = service.consolidate(memory_type, record)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                self._send_json(201, {"id": rec_id})

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path == "/retrieve":
                    new_path = "/memory"
                    if parsed.query:
                        new_path += f"?{parsed.query}"
                    self.send_response(308)
                    self.send_header("Location", new_path)
                    self.end_headers()
                    return
                if parsed.path != "/memory":
                    self.send_response(404)
                    self.end_headers()
                    return
                if not self._check_role("GET", "/memory"):
                    self._send_json(403, {"error": "forbidden"})
                    return
                params = parse_qs(parsed.query)
                memory_type = params.get("memory_type", ["episodic"])[0]
                limit = int(params.get("limit", ["5"])[0])
                data = self._json_body()
                query = data.get("query") or data.get("task_context") or {}
                try:
                    results = service.retrieve(memory_type, query, limit=limit)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                self._send_json(200, {"results": results})

        return Handler

    def serve_forever(self) -> None:  # pragma: no cover - manual run
        self.httpd.serve_forever()
