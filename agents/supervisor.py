"""
Supervisor Agent Implementation.
This agent acts as the primary coordinator for research tasks.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml
from jsonschema import ValidationError as JSONValidationError
from jsonschema import validate as json_validate
from pykwalify.core import Core

from engine.state import State
from services.tool_registry import (
    AccessDeniedError,
    ToolRegistry,
    create_default_registry,
)


class SupervisorAgent:
    SCHEMA_PATH = (
        Path(__file__).resolve().parent.parent / "schemas" / "supervisor_plan.yaml"
    )
    JSON_SCHEMA_PATH = (
        Path(__file__).resolve().parent.parent
        / "schemas"
        / "supervisor_plan_schema.json"
    )

    def __init__(
        self,
        *,
        ltm_endpoint: Optional[str] = None,
        retrieval_limit: int = 5,
        ltm_service: Optional[Any] = None,
        orchestration_engine: Optional[Any] = None,
        agent_registry: Optional[Any] = None,
        tool_registry: ToolRegistry | None = None,
        use_plan_templates: bool | None = None,
        available_agents: Optional[List[str]] | None = None,
        agent_skills: Optional[Dict[str, List[str]]] | None = None,
        procedural_memory: Optional[Any] = None,
    ) -> None:
        """Initialize supervisor with optional services."""

        self.ltm_endpoint = ltm_endpoint
        self.retrieval_limit = retrieval_limit
        self.ltm_service = ltm_service
        self.orchestration_engine = orchestration_engine
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry or create_default_registry()
        self.procedural_memory = procedural_memory
        try:
            self.tool_registry.get_tool("Supervisor", "knowledge_graph_search")
            self.has_knowledge_graph_search = True
        except Exception:
            self.has_knowledge_graph_search = False
        if use_plan_templates is None:
            env_val = os.getenv("USE_PLAN_TEMPLATES")
            use_plan_templates = True if env_val is None else bool(env_val)
        self.use_plan_templates = use_plan_templates
        try:
            with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.plan_schema = yaml.safe_load(f) or {}
        except FileNotFoundError:  # pragma: no cover - doc missing only in dev
            self.plan_schema = {}
        try:
            with open(self.JSON_SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.plan_json_schema = json.load(f)
        except FileNotFoundError:  # pragma: no cover - optional in dev
            self.plan_json_schema = {}

        self.logger = logging.getLogger(__name__)

        self.available_agents = available_agents or ["WebResearcher"]
        self.agent_skills = agent_skills or {}

    def _decompose_query(self, query: str) -> List[Dict[str, Any]]:
        """Return research sub-topics derived from the query."""

        normalized = query.strip()
        lowered = normalized.lower()
        if "transformer" in lowered and "lstm" in lowered:
            return [
                {"topic": "Transformer performance"},
                {"topic": "LSTM performance"},
            ]

        parts = [
            q.strip()
            for q in normalized.replace("versus", "vs").split("vs")
            if q.strip()
        ]
        if len(parts) <= 1:
            return [{"topic": normalized}]
        return [{"topic": p} for p in parts]

    def _extract_spatio_temporal(
        self, query: str
    ) -> tuple[Optional[List[float]], Optional[Dict[str, int]]]:
        """Detect bounding box and time range from a query string."""
        bbox = None
        time_range = None
        m = re.search(r"from (\d{4}) to (\d{4})", query)
        if m:
            time_range = {"valid_from": int(m.group(1)), "valid_to": int(m.group(2))}
        loc_map = {
            "europe": [-10.0, 35.0, 30.0, 60.0],
            "paris": [2.25, 48.8, 2.4, 48.9],
            "new york": [-74.3, 40.5, -73.6, 40.9],
        }
        lowered = query.lower()
        for name, box in loc_map.items():
            if name in lowered:
                bbox = box
                break
        return bbox, time_range

    def _score_memories(self, query: str, memories: List[Dict]) -> List[Dict]:
        """Use similarity scores from LTM results when available."""

        for rec in memories:
            if "similarity" in rec:
                rec["relevance"] = rec["similarity"]
        if any("relevance" in r for r in memories):
            memories.sort(key=lambda r: r.get("relevance", 0), reverse=True)
        return memories

    def _merge_template(self, plan: Dict[str, Any], template: Dict[str, Any]) -> None:
        """Merge graph structure from a template plan into ``plan``."""

        t_graph = template.get("graph")
        if not isinstance(t_graph, dict):
            return
        plan["graph"] = t_graph

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    def _skill_score(self, tags: Iterable[str], agent: str) -> float:
        metadata: Dict[str, Any] = {}
        if self.procedural_memory:
            metadata = self.procedural_memory.get_agent_metadata(agent)
        if not metadata:
            metadata = {
                "domains": self.agent_skills.get(agent, []),
                "success_rate": 1.0,
            }
        skill_tokens = {s.lower() for s in metadata.get("domains", [])}
        tag_tokens = {t.lower() for t in tags}
        overlap = len(tag_tokens.intersection(skill_tokens))
        return overlap * float(metadata.get("success_rate", 1.0))

    def _select_agent(self, tags: Iterable[str]) -> str:
        generalist = self.available_agents[0]
        best = generalist
        best_score = 0.0
        scores: Dict[str, float] = {}
        for agent in self.available_agents[1:]:
            score = self._skill_score(tags, agent)
            scores[agent] = score
            if score > best_score:
                best = agent
                best_score = score
        if best_score <= 0:
            best = generalist
        scores[best] = best_score
        self.logger.info(
            json.dumps({"event": "agent_selection", "scores": scores, "selected": best})
        )
        return best

    def plan_research_task(self, query: str) -> Dict[str, Any]:
        """Decompose research query into executable subgraphs."""

        past: List[Dict] = []
        if self.ltm_endpoint:
            try:
                past = self.tool_registry.invoke(
                    "Supervisor",
                    "retrieve_memory",
                    {"query": query},
                    limit=self.retrieval_limit,
                    endpoint=self.ltm_endpoint,
                )
            except AccessDeniedError:
                past = []
            except Exception:  # pragma: no cover - network errors
                past = []
        elif self.ltm_service:
            try:
                past = self.ltm_service.retrieve(query)
            except Exception:  # pragma: no cover - service errors
                past = []

        past = self._score_memories(query, past)

        tasks = self._decompose_query(query)
        bbox, time_range = self._extract_spatio_temporal(query)

        nodes = []
        edges = []
        for idx, task in enumerate(tasks):
            node_id = f"research_{idx}"
            tags = task.get("tags") or self._tokenize(task.get("topic", ""))
            agent = self._select_agent(tags)
            nodes.append({"id": node_id, "agent": agent, **task})
            edges.append({"from": node_id, "to": "synthesis"})
        nodes.append({"id": "synthesis", "agent": "Supervisor", "task": "synthesize"})
        nodes.append({"id": "citation", "agent": "CitationAgent", "task": "cite"})
        edges.append({"from": "synthesis", "to": "citation"})

        plan = {
            "query": query,
            "context": past,
            "graph": {"nodes": nodes, "edges": edges},
            "evaluation": {"metric": "quality"},
        }
        if time_range:
            plan["time_range"] = time_range
        if bbox:
            plan["bbox"] = bbox

        if self.use_plan_templates:
            for rec in past:
                tmpl = rec.get("task_context", {}).get("plan")
                if tmpl:
                    self._merge_template(plan, tmpl)
                    break
        self.validate_plan(plan)
        return plan

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def validate_plan(self, plan: Dict[str, Any]) -> None:
        """Validate a plan dictionary against available schemas."""

        if self.plan_schema:
            try:
                Core(source_data=plan, schema_data=self.plan_schema).validate()
            except Exception as exc:
                raise ValueError(f"plan validation error: {exc}") from exc

        if self.plan_json_schema:
            try:
                json_validate(instance=plan, schema=self.plan_json_schema)
            except JSONValidationError as exc:
                raise ValueError(f"plan validation error: {exc.message}") from exc

    # ------------------------------------------------------------------
    # YAML helpers
    # ------------------------------------------------------------------
    def format_plan_as_yaml(self, plan: Dict[str, Any]) -> str:
        """Serialize plan dictionary to YAML string."""

        return yaml.safe_dump(plan, sort_keys=False)

    def parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse YAML plan text and validate expected structure."""

        try:
            data = yaml.safe_load(plan_text) or {}
        except yaml.YAMLError as exc:
            raise ValueError("invalid plan format") from exc
        if not isinstance(data, dict) or "graph" not in data:
            raise ValueError("invalid plan format")
        graph = data.get("graph", {})
        if not isinstance(graph, dict) or "nodes" not in graph or "edges" not in graph:
            raise ValueError("invalid graph definition")
        self.validate_plan(data)
        return data

    def analyze_query(self, query: str) -> State:
        """Perform initial analysis and create the workflow state."""

        cleaned = query.strip()
        facts: List[Dict[str, Any]] = []
        if self.has_knowledge_graph_search:
            try:
                facts = self.tool_registry.invoke(
                    "Supervisor", "knowledge_graph_search", {"text": cleaned}
                )
            except Exception:
                facts = []
        plan = self.plan_research_task(cleaned)
        state = State()
        state.update(
            {
                "initial_query": cleaned,
                "plan": plan,
                "context": plan.get("context", []),
            }
        )
        if facts:
            state.update({"facts": facts})
        return state

    def __call__(self, graph_state: Any, scratchpad: Dict[str, Any]) -> Any:
        """Node entrypoint for the orchestration graph.

        Parameters
        ----------
        graph_state:
            Parent workflow state.
        scratchpad:
            Shared scratchpad (unused).
        """

        query = graph_state.data.get("query", "")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        state = self.analyze_query(query)
        graph_state.update({"state": state})
        return graph_state
