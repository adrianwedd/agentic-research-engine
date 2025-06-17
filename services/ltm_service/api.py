from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse

try:
    from pydantic import BaseModel, Field, ValidationError

    _HAS_PYDANTIC = True
except Exception:  # pragma: no cover - fallback for test stubs
    _HAS_PYDANTIC = False

    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        @classmethod
        def model_rebuild(cls):
            pass

    def Field(default=None, **_):
        return default

    class ValidationError(Exception):
        """Fallback validation error when pydantic isn't fully available."""

        pass


from services.monitoring.system_monitor import SystemMonitor

from .episodic_memory import EpisodicMemoryService
from .procedural_memory import ProceduralMemoryService
from .semantic_memory import SemanticMemoryService, SpatioTemporalMemoryService

ALLOWED_MEMORY_TYPES: Set[str] = {"episodic", "semantic", "procedural"}

ROLE_PERMISSIONS: Dict[Tuple[str, str], Set[str]] = {
    ("POST", "/memory"): {"editor"},
    ("POST", "/semantic_consolidate"): {"editor"},
    ("POST", "/temporal_consolidate"): {"editor"},
    ("POST", "/propagate_subgraph"): {"editor"},
    ("GET", "/memory"): {"viewer", "editor"},
    ("GET", "/spatial_query"): {"viewer", "editor"},
    ("DELETE", "/forget"): {"editor"},
    # Deprecated paths kept for one release cycle
    ("POST", "/consolidate"): {"editor"},
    ("GET", "/retrieve"): {"viewer", "editor"},
}


if _HAS_PYDANTIC:

    class ConsolidateRequest(BaseModel):
        record: Dict = Field(...)
        memory_type: str = Field("episodic")

else:  # pragma: no cover - used in tests without pydantic

    @dataclass
    class ConsolidateRequest:
        record: Dict
        memory_type: str = "episodic"


if _HAS_PYDANTIC:

    class RetrieveBody(BaseModel):
        query: Optional[Dict] = None
        task_context: Optional[Dict] = None

else:  # pragma: no cover

    @dataclass
    class RetrieveBody:
        query: Optional[Dict] = None
        task_context: Optional[Dict] = None


if _HAS_PYDANTIC:

    class TemporalConsolidateRequest(BaseModel):
        subject: str
        predicate: str
        object: str
        value: Any | None = None
        valid_from: float
        valid_to: float | None = None
        location: Any | None = None

else:  # pragma: no cover

    @dataclass
    class TemporalConsolidateRequest:
        subject: str
        predicate: str
        object: str
        value: Any | None = None
        valid_from: float = 0.0
        valid_to: float | None = None
        location: Any | None = None


if _HAS_PYDANTIC:

    class ForgetRequest(BaseModel):
        hard: bool = False

else:  # pragma: no cover

    @dataclass
    class ForgetRequest:
        hard: bool = False


class LTMService:
    """Coordinate access to various memory modules."""

    def __init__(
        self,
        episodic_memory: EpisodicMemoryService,
        semantic_memory: SemanticMemoryService | None = None,
        procedural_memory: ProceduralMemoryService | None = None,
        monitor: SystemMonitor | None = None,
    ) -> None:
        self._modules: Dict[str, object] = {"episodic": episodic_memory}
        self._modules["semantic"] = semantic_memory or SemanticMemoryService()
        self._modules["procedural"] = procedural_memory or ProceduralMemoryService(
            episodic_memory.storage
        )
        self._monitor = monitor

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
        if memory_type == "procedural":
            return module.store_procedure(
                record.get("task_context", {}),
                record.get("procedure", []),
                record.get("outcome", {}),
            )
        raise ValueError(f"Unsupported memory type: {memory_type}")

    def semantic_consolidate(
        self, payload: Dict | str, *, fmt: str = "jsonld"
    ) -> List[str] | List[Dict[str, Any]]:
        module: SemanticMemoryService = self._modules.get("semantic")  # type: ignore[assignment]
        if module is None:
            raise ValueError("Semantic memory module not available")
        if fmt == "cypher":
            if not isinstance(payload, str):
                raise ValueError("Cypher payload must be a string")
            return module.run_cypher(payload)
        if not isinstance(payload, dict):
            raise ValueError("JSON-LD payload must be a dictionary")
        return module.store_jsonld(payload)

    def propagate_subgraph(self, subgraph: Dict[str, Any]) -> List[str]:
        """Store all relations from a subgraph into semantic memory."""
        module: SemanticMemoryService = self._modules.get("semantic")  # type: ignore[assignment]
        if module is None:
            raise ValueError("Semantic memory module not available")
        ids: List[str] = []
        for rel in subgraph.get("relations", []):
            ids.append(
                module.store_fact(
                    rel.get("subject"),
                    rel.get("predicate"),
                    rel.get("object"),
                    properties=rel.get("properties", {}),
                )
            )
        return ids

    def temporal_consolidate(self, fact: Dict[str, Any]) -> str:
        """Merge a fact version into spatio-temporal memory."""
        module = self._modules.get("semantic")
        if not isinstance(module, SpatioTemporalMemoryService):
            raise ValueError("Spatio-temporal memory module not available")
        return module.merge_version(
            fact["subject"],
            fact["predicate"],
            fact["object"],
            value=fact.get("value"),
            valid_from=fact["valid_from"],
            valid_to=fact.get("valid_to"),
            location=fact.get("location"),
        )


    def spatial_query(
        self, bbox: List[float], valid_from: float, valid_to: float
    ) -> List[Dict[str, Any]]:
        module = self._modules.get("semantic")
        if not isinstance(module, SpatioTemporalMemoryService):
            raise ValueError("Spatio-temporal memory module not available")
        return module.query_spatial_range(bbox, valid_from, valid_to)

    def retrieve(self, memory_type: str, query: Dict, *, limit: int = 5) -> List[Dict]:
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        if memory_type == "episodic":
            results = module.retrieve_similar_experiences(query, limit=limit)
        elif memory_type == "semantic":
            results = module.query_facts(**query)[:limit]
        elif memory_type == "procedural":
            results = module.retrieve_similar_procedures(query, limit=limit)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

        if self._monitor:
            self._monitor.record_ltm_result(memory_type, bool(results))
        return results

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
        if memory_type == "procedural":
            if hasattr(module, "forget_procedure"):
                return module.forget_procedure(identifier, hard=hard)
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

        def _rbac(method: str, path: str):
            """Decorator enforcing role-based access for Handler methods."""

            def decorator(func):
                def wrapped(self, *args, **kwargs):
                    if not self._check_role(method, path):
                        self._send_json(403, {"error": "forbidden"})
                        return
                    return func(self, *args, **kwargs)

                return wrapped

            return decorator

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
                if parsed.path == "/propagate_subgraph":
                    if not self._check_role("POST", "/propagate_subgraph"):
                        self._send_json(403, {"error": "forbidden"})
                        return
                    data = self._json_body()
                    try:
                        ids = service.propagate_subgraph(data)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"ids": ids})
                    return
                if parsed.path == "/semantic_consolidate":
                    if not self._check_role("POST", "/semantic_consolidate"):
                        self._send_json(403, {"error": "forbidden"})
                        return
                    data = self._json_body()
                    payload = data.get("payload")
                    fmt = data.get("format", "jsonld")
                    try:
                        result = service.semantic_consolidate(payload, fmt=fmt)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(201, {"result": result})
                    return
                if parsed.path == "/temporal_consolidate":
                    if not self._check_role("POST", "/temporal_consolidate"):
                        self._send_json(403, {"error": "forbidden"})
                        return
                    data = self._json_body()
                    try:
                        req = TemporalConsolidateRequest(**data)
                        fact = getattr(req, "model_dump", req.__dict__)()
                        fid = service.temporal_consolidate(fact)
                    except (ValidationError, ValueError) as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(201, {"id": fid})
                    return
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
                if parsed.path == "/spatial_query":
                    if not self._check_role("GET", "/spatial_query"):
                        self._send_json(403, {"error": "forbidden"})
                        return
                    params = parse_qs(parsed.query)
                    bbox_str = params.get("bbox", [""])[0]
                    try:
                        bbox = [float(x) for x in bbox_str.split(",")]
                        if len(bbox) != 4:
                            raise ValueError
                        valid_from = float(params.get("valid_from", ["0"])[0])
                        valid_to = float(params.get("valid_to", ["0"])[0])
                    except ValueError:
                        self._send_json(400, {"error": "invalid parameters"})
                        return
                    try:
                        results = service.spatial_query(bbox, valid_from, valid_to)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"results": results})
                    return
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
