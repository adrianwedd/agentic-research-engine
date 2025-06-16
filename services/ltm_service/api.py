from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, ValidationError

from .episodic_memory import EpisodicMemoryService
from .semantic_memory import SemanticMemoryService

ALLOWED_MEMORY_TYPES: Set[str] = {"episodic", "semantic", "procedural"}

ROLE_PERMISSIONS: Dict[Tuple[str, str], Set[str]] = {
    ("POST", "/memory"): {"editor"},
    ("GET", "/memory"): {"viewer", "editor"},
    ("DELETE", "/forget"): {"editor"},
    # Deprecated paths kept for one release cycle
    ("POST", "/consolidate"): {"editor"},
    ("GET", "/retrieve"): {"viewer", "editor"},
}


class ConsolidateRequest(BaseModel):
    record: Dict = Field(...)
    memory_type: str = Field("episodic")


class RetrieveBody(BaseModel):
    query: Optional[Dict] = None
    task_context: Optional[Dict] = None


class ForgetRequest(BaseModel):
    hard: bool = False


class LTMService:
    """Coordinate access to various memory modules."""

    def __init__(
        self,
        episodic_memory: EpisodicMemoryService,
        semantic_memory: SemanticMemoryService | None = None,
    ) -> None:
        self._modules: Dict[str, object] = {"episodic": episodic_memory}
        self._modules["semantic"] = semantic_memory or SemanticMemoryService()

    def consolidate(self, memory_type: str, record: Dict) -> str:
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        if memory_type == "episodic":
            return module.store_experience(
                record.get("task_context", {}),
                record.get("execution_trace", {}),
                record.get("outcome", {}),
            )
        if memory_type == "semantic":
            return module.store_fact(
                record["subject"],
                record["predicate"],
                record["object"],
                properties=record.get("properties", {}),
            )
        raise ValueError(f"Unsupported memory type: {memory_type}")

    def retrieve(self, memory_type: str, query: Dict, *, limit: int = 5) -> List[Dict]:
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        if memory_type == "episodic":
            return module.retrieve_similar_experiences(query, limit=limit)
        if memory_type == "semantic":
            return module.query_facts(**query)[:limit]
        raise ValueError(f"Unsupported memory type: {memory_type}")

    def forget(self, memory_type: str, identifier: str, *, hard: bool = False) -> bool:
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        if memory_type == "episodic":
            if hasattr(module, "forget_experience"):
                return module.forget_experience(identifier, hard=hard)
        if memory_type == "semantic":
            if hasattr(module, "forget_fact"):
                return module.forget_fact(identifier, hard=hard)
        raise ValueError(f"Unsupported memory type: {memory_type}")


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
            def _rbac(self, method: str, path: str):
                def decorator(func):
                    def wrapped(*args, **kwargs):
                        if not self._check_role(method, path):
                            self._send_json(403, {"error": "forbidden"})
                            return
                        return func(*args, **kwargs)

                    return wrapped

                return decorator

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

            @_rbac("POST", "/memory")
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
                data = self._json_body()
                try:
                    req = ConsolidateRequest(**data)
                except ValidationError as exc:
                    self._send_json(422, {"error": exc.errors()})
                    return
                try:
                    rec_id = service.consolidate(req.memory_type, req.record)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                self._send_json(201, {"id": rec_id})

            @_rbac("GET", "/memory")
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
                params = parse_qs(parsed.query)
                memory_type = params.get("memory_type", ["episodic"])[0]
                limit = int(params.get("limit", ["5"])[0])
                data = self._json_body()
                try:
                    body = RetrieveBody(**data)
                except ValidationError as exc:
                    self._send_json(422, {"error": exc.errors()})
                    return
                query = body.query or body.task_context or {}
                try:
                    results = service.retrieve(memory_type, query, limit=limit)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                self._send_json(200, {"results": results})

            @_rbac("DELETE", "/forget")
            def do_DELETE(self) -> None:
                parsed = urlparse(self.path)
                if not parsed.path.startswith("/forget/"):
                    self.send_response(404)
                    self.end_headers()
                    return
                identifier = parsed.path.split("/", 2)[2]
                params = parse_qs(parsed.query)
                memory_type = params.get("memory_type", ["episodic"])[0]
                data = self._json_body()
                try:
                    req = ForgetRequest(**data)
                except ValidationError as exc:
                    self._send_json(422, {"error": exc.errors()})
                    return
                try:
                    success = service.forget(memory_type, identifier, hard=req.hard)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                if not success:
                    self._send_json(404, {"error": "not found"})
                    return
                self._send_json(200, {"status": "forgotten"})

        return Handler

    def serve_forever(self) -> None:  # pragma: no cover - manual run
        self.httpd.serve_forever()
