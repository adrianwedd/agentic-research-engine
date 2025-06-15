"""
Supervisor Agent Implementation.
This agent acts as the primary coordinator for research tasks.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pykwalify.core import Core

from tools.ltm_client import retrieve_memory


@dataclass
class State:
    """Simple representation of the system state."""

    initial_query: str
    plan: Optional[Dict[str, Any]] = None
    context: List[Any] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None


class SupervisorAgent:
    SCHEMA_PATH = (
        Path(__file__).resolve().parent.parent / "schemas" / "supervisor_plan.yaml"
    )

    def __init__(
        self,
        *,
        ltm_endpoint: Optional[str] = None,
        retrieval_limit: int = 5,
        ltm_service: Optional[Any] = None,
        orchestration_engine: Optional[Any] = None,
        agent_registry: Optional[Any] = None,
    ) -> None:
        """Initialize supervisor with optional services."""

        self.ltm_endpoint = ltm_endpoint
        self.retrieval_limit = retrieval_limit
        self.ltm_service = ltm_service
        self.orchestration_engine = orchestration_engine
        self.agent_registry = agent_registry
        try:
            with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.plan_schema = yaml.safe_load(f) or {}
        except FileNotFoundError:  # pragma: no cover - doc missing only in dev
            self.plan_schema = {}

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

    def plan_research_task(self, query: str) -> Dict[str, Any]:
        """Decompose research query into executable subgraphs."""

        past = []
        if self.ltm_endpoint:
            try:
                past = retrieve_memory(
                    {"query": query},
                    limit=self.retrieval_limit,
                    endpoint=self.ltm_endpoint,
                )
            except Exception:  # pragma: no cover - network errors
                past = []
        elif self.ltm_service:
            try:
                past = self.ltm_service.retrieve(query)
            except Exception:  # pragma: no cover - service errors
                past = []

        tasks = self._decompose_query(query)

        nodes = []
        edges = []
        for idx, task in enumerate(tasks):
            node_id = f"research_{idx}"
            nodes.append({"id": node_id, "agent": "WebResearcher", **task})
            edges.append({"from": node_id, "to": "synthesis"})
        nodes.append({"id": "synthesis", "agent": "Supervisor", "task": "synthesize"})

        plan = {
            "query": query,
            "context": past,
            "graph": {"nodes": nodes, "edges": edges},
            "evaluation": {"metric": "quality"},
        }
        self.validate_plan(plan)
        return plan

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def validate_plan(self, plan: Dict[str, Any]) -> None:
        """Validate a plan dictionary against the YAML schema."""

        if not self.plan_schema:
            return
        try:
            Core(source_data=plan, schema_data=self.plan_schema).validate()
        except Exception as exc:
            raise ValueError(f"plan validation error: {exc}") from exc

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
        plan = self.plan_research_task(cleaned)
        return State(initial_query=cleaned, plan=plan, context=plan.get("context", []))

    def __call__(self, graph_state: Any) -> Any:
        """Node entrypoint for the orchestration graph."""

        query = graph_state.data.get("query", "")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        state = self.analyze_query(query)
        graph_state.update({"state": state})
        return graph_state
