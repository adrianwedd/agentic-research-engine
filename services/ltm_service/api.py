from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse

try:
    from pydantic import BaseModel, Field, ValidationError, field_validator

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
from .skill_library import SkillLibrary

ALLOWED_MEMORY_TYPES: Set[str] = {"episodic", "semantic", "procedural", "evaluator"}


def validate_memory_type(memory_type: str) -> None:
    if memory_type not in ALLOWED_MEMORY_TYPES:
        raise ValueError("invalid memory type")


SUSPICIOUS_PATTERNS: List[str] = ["AGENTPOISON", "TRIGGER PHRASE"]

ROLE_PERMISSIONS: Dict[Tuple[str, str], Set[str]] = {
    ("POST", "/memory"): {"editor"},
    ("POST", "/semantic_consolidate"): {"editor"},
    ("POST", "/temporal_consolidate"): {"editor"},
    ("POST", "/propagate_subgraph"): {"editor"},
    ("GET", "/memory"): {"viewer", "editor"},
    ("GET", "/spatial_query"): {"viewer", "editor"},
    ("POST", "/skill"): {"editor"},
    ("POST", "/skill_vector_query"): {"viewer", "editor"},
    ("POST", "/skill_metadata_query"): {"viewer", "editor"},
    ("DELETE", "/forget"): {"editor"},
    ("POST", "/evaluator_memory"): {"editor"},
    ("GET", "/evaluator_memory"): {"viewer", "editor"},
    ("DELETE", "/forget_evaluator"): {"editor"},
    ("GET", "/provenance"): {"viewer", "editor"},
    # Deprecated paths kept for one release cycle
    ("POST", "/consolidate"): {"editor"},
    ("GET", "/retrieve"): {"viewer", "editor"},
}


if _HAS_PYDANTIC:

    class ConsolidateRequest(BaseModel):
        record: Dict = Field(...)
        memory_type: str = Field("episodic")

        @field_validator("memory_type")
        @classmethod
        def _validate_memory_type(cls, v: str) -> str:
            validate_memory_type(v)
            return v

else:  # pragma: no cover - used in tests without pydantic

    @dataclass
    class ConsolidateRequest:
        record: Dict
        memory_type: str = "episodic"

        def __post_init__(self) -> None:
            validate_memory_type(self.memory_type)


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

    class SkillRequest(BaseModel):
        skill_policy: Dict
        skill_representation: str | List[float]
        skill_metadata: Dict = Field(default_factory=dict)

    class SkillQuery(BaseModel):
        query: str | List[float] | Dict
        limit: int = 5

else:  # pragma: no cover

    @dataclass
    class ForgetRequest:
        hard: bool = False

    @dataclass
    class SkillRequest:
        skill_policy: Dict
        skill_representation: str | List[float]
        skill_metadata: Dict

    @dataclass
    class SkillQuery:
        query: str | List[float] | Dict
        limit: int = 5


class LTMService:
    """Coordinate access to various memory modules."""

    def __init__(
        self,
        episodic_memory: EpisodicMemoryService,
        semantic_memory: SemanticMemoryService | None = None,
        procedural_memory: ProceduralMemoryService | None = None,
        evaluator_memory: EpisodicMemoryService | None = None,
        monitor: SystemMonitor | None = None,
        *,
        credibility_func: Callable[[str], float] | None = None,
        credibility_threshold: float | None = None,
    ) -> None:
        self._modules: Dict[str, object] = {"episodic": episodic_memory}
        self._modules["semantic"] = semantic_memory or SemanticMemoryService()
        self._modules["procedural"] = procedural_memory or ProceduralMemoryService(
            episodic_memory.storage
        )
        self._modules["evaluator"] = evaluator_memory or EpisodicMemoryService(
            episodic_memory.storage
        )
        self.skill_library = SkillLibrary()
        self._monitor = monitor
        self._credibility_func = credibility_func or (lambda src: 1.0)
        self._cred_threshold = (
            credibility_threshold
            if credibility_threshold is not None
            else float(os.getenv("LTM_CREDIBILITY_THRESHOLD", "0.5"))
        )
        self.verification_log: List[Dict[str, Any]] = []
        self.quarantine_log: List[Dict[str, Any]] = []

    def _verify_source(self, source: str, record: Dict | None = None) -> bool:
        score = float(self._credibility_func(source))
        passed = score >= self._cred_threshold
        ts = time.time()
        entry = {
            "source": source,
            "score": score,
            "passed": passed,
            "timestamp": ts,
        }
        self.verification_log.append(entry)
        if not passed:
            self.quarantine_log.append(
                {
                    "source": source,
                    "score": score,
                    "record": record,
                    "timestamp": ts,
                }
            )
        return passed

    def _has_suspicious(self, value: Any) -> bool:
        if isinstance(value, str):
            lower = value.lower()
            return any(p.lower() in lower for p in SUSPICIOUS_PATTERNS)
        if isinstance(value, dict):
            return any(self._has_suspicious(v) for v in value.values())
        if isinstance(value, list):
            return any(self._has_suspicious(v) for v in value)
        return False

    def _strip_suspicious(self, value: Any) -> Any:
        if isinstance(value, str):
            cleaned = value
            for p in SUSPICIOUS_PATTERNS:
                cleaned = cleaned.replace(p, "[REDACTED]")
                cleaned = cleaned.replace(p.lower(), "[REDACTED]")
            return cleaned
        if isinstance(value, dict):
            return {k: self._strip_suspicious(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._strip_suspicious(v) for v in value]
        return value

    def _sanitize_records(
        self, items: List[Dict[str, Any]], memory_type: str, query: Dict | None = None
    ) -> List[Dict[str, Any]]:
        """Remove suspicious patterns from ``items`` and log quarantined entries."""

        sanitized: List[Dict[str, Any]] = []
        for item in items:
            if self._has_suspicious(item):
                self.quarantine_log.append(
                    {
                        "memory_type": memory_type,
                        "query": query,
                        "item": item,
                        "timestamp": time.time(),
                    }
                )
                item = self._strip_suspicious(item)
            sanitized.append(item)
        return sanitized

    def consolidate(self, memory_type: str, record: Dict) -> str:
        validate_memory_type(memory_type)
        module = self._modules.get(memory_type)
        if module is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        source = record.get("source")
        if isinstance(source, str) and not self._verify_source(source, record):
            raise ValueError("source credibility below threshold")
        provenance = {
            "source": source,
            "ingestion_date": record.get("ingestion_date", time.time()),
            "transformations": record.get("transformations", []),
        }
        if memory_type == "episodic":
            return module.store_experience(
                record.get("task_context", {}),
                record.get("execution_trace", {}),
                record.get("outcome", {}),
                provenance=provenance,
            )
        if memory_type == "semantic":
            return module.store_fact(
                record["subject"],
                record["predicate"],
                record["object"],
                properties=record.get("properties", {}),
                provenance=provenance,
            )
        if memory_type == "procedural":
            return module.store_procedure(
                record.get("task_context", {}),
                record.get("procedure", []),
                record.get("outcome", {}),
                provenance=provenance,
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
        results = module.query_spatial_range(bbox, valid_from, valid_to)
        return self._sanitize_records(
            results,
            "spatio-temporal",
            {
                "bbox": bbox,
                "valid_from": valid_from,
                "valid_to": valid_to,
            },
        )

    def add_skill(
        self,
        policy: Dict[str, Any],
        representation: str | List[float],
        metadata: Dict[str, Any],
    ) -> str:
        return self.skill_library.add_skill(policy, representation, metadata)

    def skill_vector_query(
        self, query: str | List[float], *, limit: int = 5
    ) -> List[Dict[str, Any]]:
        results = self.skill_library.query_by_vector(query, limit=limit)
        return self._sanitize_records(results, "skill", {"query": query})

    def skill_metadata_query(
        self, metadata: Dict[str, Any], *, limit: int = 5
    ) -> List[Dict[str, Any]]:
        results = self.skill_library.query_by_metadata(metadata, limit=limit)
        return self._sanitize_records(results, "skill", metadata)

    def store_evaluator_memory(self, critique: Dict[str, Any]) -> str:
        module: EpisodicMemoryService = self._modules["evaluator"]  # type: ignore[assignment]
        return module.store_experience({"prompt": critique.get("prompt")}, {}, critique)

    def retrieve_evaluator_memory(
        self, query: Dict[str, Any], *, limit: int = 5
    ) -> List[Dict]:
        module: EpisodicMemoryService = self._modules["evaluator"]  # type: ignore[assignment]
        results = module.retrieve_similar_experiences(query, limit=limit)
        return self._sanitize_records(results, "evaluator", query)

    def forget_evaluator_memory(self, identifier: str, *, hard: bool = False) -> bool:
        module: EpisodicMemoryService = self._modules["evaluator"]  # type: ignore[assignment]
        return module.forget_experience(identifier, hard=hard)

    def retrieve(self, memory_type: str, query: Dict, *, limit: int = 5) -> List[Dict]:
        validate_memory_type(memory_type)
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

        sanitized = self._sanitize_records(results, memory_type, query)

        if self._monitor:
            self._monitor.record_ltm_result(memory_type, bool(sanitized))
        return sanitized

    def get_provenance(self, memory_type: str, identifier: str) -> Dict:
        validate_memory_type(memory_type)
        module = self._modules.get(memory_type)
        if module is None or not hasattr(module, "get_provenance"):
            raise ValueError(f"Unknown memory type: {memory_type}")
        return module.get_provenance(identifier)

    def forget(self, memory_type: str, identifier: str, *, hard: bool = False) -> bool:
        validate_memory_type(memory_type)
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
                allowed = ROLE_PERMISSIONS.get((method, path))
                if allowed is None:
                    return False
                return role in allowed

            @staticmethod
            def _perm_path(path: str) -> str:
                if path.startswith("/provenance/"):
                    return "/provenance"
                if path.startswith("/forget_evaluator/"):
                    return "/forget_evaluator"
                if path.startswith("/forget/"):
                    return "/forget"
                return path

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                if not self._check_role("POST", self._perm_path(parsed.path)):
                    self._send_json(403, {"error": "forbidden"})
                    return
                if parsed.path == "/propagate_subgraph":
                    data = self._json_body()
                    try:
                        ids = service.propagate_subgraph(data)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"ids": ids})
                    return
                if parsed.path == "/semantic_consolidate":
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
                if parsed.path == "/skill":
                    data = self._json_body()
                    try:
                        req = SkillRequest(**data)
                        sid = service.add_skill(
                            req.skill_policy,
                            req.skill_representation,
                            req.skill_metadata,
                        )
                    except (ValidationError, ValueError) as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(201, {"id": sid})
                    return
                if parsed.path == "/skill_vector_query":
                    data = self._json_body()
                    try:
                        req = SkillQuery(**data)
                        results = service.skill_vector_query(req.query, limit=req.limit)
                    except (ValidationError, ValueError) as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"results": results})
                    return
                if parsed.path == "/skill_metadata_query":
                    data = self._json_body()
                    try:
                        req = SkillQuery(**data)
                        if not isinstance(req.query, dict):
                            raise ValueError("metadata query must be dict")
                        results = service.skill_metadata_query(
                            req.query, limit=req.limit
                        )
                    except (ValidationError, ValueError) as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"results": results})
                    return
                if parsed.path == "/evaluator_memory":
                    data = self._json_body()
                    critique = data.get("critique")
                    if critique is None:
                        self._send_json(422, {"error": "critique required"})
                        return
                    try:
                        cid = service.store_evaluator_memory(critique)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(201, {"id": cid})
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
                data = self._json_body()
                try:
                    req = ConsolidateRequest(**data)
                except ValidationError as exc:
                    self._send_json(422, {"error": exc.errors()})
                    return
                try:
                    validate_memory_type(req.memory_type)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                try:
                    rec_id = service.consolidate(req.memory_type, req.record)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                self._send_json(201, {"id": rec_id})

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if not self._check_role("GET", self._perm_path(parsed.path)):
                    self._send_json(403, {"error": "forbidden"})
                    return
                if parsed.path == "/spatial_query":
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
                if parsed.path == "/evaluator_memory":
                    params = parse_qs(parsed.query)
                    limit = int(params.get("limit", ["5"])[0])
                    data = self._json_body()
                    query = (data.get("query") if isinstance(data, dict) else {}) or {}
                    try:
                        results = service.retrieve_evaluator_memory(query, limit=limit)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"results": results})
                    return
                if parsed.path.startswith("/provenance/"):
                    parts = parsed.path.split("/")
                    if len(parts) < 4:
                        self._send_json(404, {"error": "not found"})
                        return
                    memory_type = parts[2]
                    identifier = parts[3]
                    try:
                        validate_memory_type(memory_type)
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    try:
                        prov = service.get_provenance(memory_type, identifier)
                    except KeyError:
                        self._send_json(404, {"error": "not found"})
                        return
                    except ValueError as exc:
                        self._send_json(400, {"error": str(exc)})
                        return
                    self._send_json(200, {"provenance": prov})
                    return
                if parsed.path != "/memory":
                    self.send_response(404)
                    self.end_headers()
                    return
                params = parse_qs(parsed.query)
                memory_type = params.get("memory_type", ["episodic"])[0]
                try:
                    validate_memory_type(memory_type)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
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

            def do_DELETE(self) -> None:
                parsed = urlparse(self.path)
                if not self._check_role("DELETE", self._perm_path(parsed.path)):
                    self._send_json(403, {"error": "forbidden"})
                    return
                if parsed.path.startswith("/forget_evaluator/"):
                    identifier = parsed.path.split("/", 2)[2]
                    data = self._json_body()
                    hard = bool(data.get("hard"))
                    success = service.forget_evaluator_memory(identifier, hard=hard)
                    if not success:
                        self._send_json(404, {"error": "not found"})
                        return
                    self._send_json(200, {"status": "forgotten"})
                    return
                if not parsed.path.startswith("/forget/"):
                    self.send_response(404)
                    self.end_headers()
                    return
                identifier = parsed.path.split("/", 2)[2]
                params = parse_qs(parsed.query)
                memory_type = params.get("memory_type", ["episodic"])[0]
                try:
                    validate_memory_type(memory_type)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
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
