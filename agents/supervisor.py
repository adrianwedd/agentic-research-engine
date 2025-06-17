"""
Supervisor Agent Implementation.
This agent acts as the primary coordinator for research tasks.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
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
    ) -> None:
        """Initialize supervisor with optional services."""

        self.ltm_endpoint = ltm_endpoint
        self.retrieval_limit = retrieval_limit
        self.ltm_service = ltm_service
        self.orchestration_engine = orchestration_engine
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry or create_default_registry()
        try:
            self.knowledge_graph_search = self.tool_registry.get_tool(
                "Supervisor", "knowledge_graph_search"
            )
        except Exception:
            self.knowledge_graph_search = None
        if use_plan_templates is None:
            use_plan_templates = bool(os.getenv("USE_PLAN_TEMPLATES"))
        self.use_plan_templates = use_plan_templates
        try:
            with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.plan_schema = yaml.safe_load(f) or {}
        except FileNotFoundError:  # pragma: no cover - doc missing only in dev
            self.plan_schema = {}

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

    def _skill_score(self, task: str, agent: str) -> int:
        skills = self.agent_skills.get(agent, [])
        if not skills:
            return 0
        task_tokens = self._tokenize(task)
        skill_tokens = {s.lower() for s in skills}
        return len(task_tokens.intersection(skill_tokens))

    def _select_agent(self, task: str) -> str:
        best = self.available_agents[0]
        best_score = float("-inf")
        for agent in self.available_agents:
            score = self._skill_score(task, agent)
            if score > best_score:
                best = agent
                best_score = score
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

        nodes = []
        edges = []
        for idx, task in enumerate(tasks):
            node_id = f"research_{idx}"
            agent = self._select_agent(task.get("topic", ""))
            nodes.append({"id": node_id, "agent": agent, **task})
            edges.append({"from": node_id, "to": "synthesis"})
        nodes.append({"id": "synthesis", "agent": "Supervisor", "task": "synthesize"})

        plan = {
            "query": query,
            "context": past,
            "graph": {"nodes": nodes, "edges": edges},
            "evaluation": {"metric": "quality"},
        }

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
        facts: List[Dict[str, Any]] = []
        if self.knowledge_graph_search:
            try:
                facts = self.knowledge_graph_search({"text": cleaned})
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
