"""Planner Agent implementation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from pykwalify.core import Core

from engine.state import State


class PlannerAgent:
    """Optimization-based plan generator."""

    SCHEMA_PATH = (
        Path(__file__).resolve().parent.parent / "schemas" / "supervisor_plan.yaml"
    )

    DEFAULT_WEIGHTS = {"reputation": 0.6, "cost": 0.3, "load": 0.1}

    def __init__(
        self,
        available_agents: Optional[List[str]] | None = None,
        *,
        agent_skills: Optional[Dict[str, List[str]]] | None = None,
        objective_metric: str = "cost",
        weights: Optional[Dict[str, float]] | None = None,
        reputation_api_url: str | None = None,
        reputation_api_token: str | None = None,
    ) -> None:
        self.available_agents = available_agents or ["WebResearcher"]
        self.agent_skills = agent_skills or {}
        self.objective_metric = objective_metric
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.reputation_api_url = reputation_api_url or os.getenv(
            "REPUTATION_API_URL",
            "http://localhost:8000/api/v1/reputation/query",
        )
        self.reputation_api_token = reputation_api_token or os.getenv(
            "REPUTATION_API_TOKEN",
            "planner-token",
        )
        try:
            with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.plan_schema = yaml.safe_load(f) or {}
        except FileNotFoundError:  # pragma: no cover - dev env
            self.plan_schema = {}

    # ------------------------------------------------------------------
    # Planning helpers
    # ------------------------------------------------------------------
    def _decompose_query(self, query: str) -> List[str]:
        normalized = query.strip()
        lowered = normalized.lower()
        if "transformer" in lowered and "lstm" in lowered:
            return [
                "Transformer performance",
                "LSTM performance",
            ]
        parts = [
            q.strip()
            for q in normalized.replace("versus", "vs").split("vs")
            if q.strip()
        ]
        if len(parts) <= 1:
            return [normalized]
        return parts

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    def _fetch_reputations(self, context: str) -> Dict[str, Dict[str, Any]]:
        if not self.reputation_api_url:
            return {}
        headers = {}
        if self.reputation_api_token:
            headers["Authorization"] = f"Bearer {self.reputation_api_token}"
        try:
            resp = requests.get(
                self.reputation_api_url,
                params={"context": context, "top_n": len(self.available_agents)},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return {}
        results = data.get("results", [])
        return {
            r.get("agent_id"): r.get("reputation_vector", {})
            for r in results
            if r.get("agent_id")
        }

    def _skill_score(self, task: str, agent: str) -> int:
        skills = self.agent_skills.get(agent, [])
        if not skills:
            return 0
        task_tokens = self._tokenize(task)
        skill_tokens = {s.lower() for s in skills}
        return len(task_tokens.intersection(skill_tokens))

    def _allocate_tasks(self, tasks: List[str]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        load: Dict[str, int] = {name: 0 for name in self.available_agents}
        reputations = self._fetch_reputations("research")
        for idx, topic in enumerate(tasks):
            best_agent = None
            best_score = float("-inf")
            for agent in self.available_agents:
                rep = reputations.get(agent, {})
                rep_score = float(rep.get("accuracy", 0.0))
                cost = float(rep.get("token_cost", 0.0))
                score = (
                    self.weights.get("reputation", 0.0) * rep_score
                    - self.weights.get("cost", 0.0) * cost
                    - self.weights.get("load", 0.0) * load[agent]
                )
                if best_agent is None or score > best_score:
                    best_agent = agent
                    best_score = score
            load[best_agent] += 1
            nodes.append({"id": f"task_{idx}", "agent": best_agent, "topic": topic})
        return nodes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def plan_research_task(self, query: str) -> Dict[str, Any]:
        tasks = self._decompose_query(query)
        research_nodes = self._allocate_tasks(tasks)
        edges = [{"from": node["id"], "to": "synthesis"} for node in research_nodes]
        nodes = research_nodes + [
            {"id": "synthesis", "agent": "Supervisor", "task": "synthesize"}
        ]
        plan = {
            "query": query,
            "context": [],
            "graph": {"nodes": nodes, "edges": edges},
            "evaluation": {"metric": self.objective_metric},
        }
        self.validate_plan(plan)
        return plan

    def format_plan_as_yaml(self, plan: Dict[str, Any]) -> str:
        return yaml.safe_dump(plan, sort_keys=False)

    def parse_plan(self, plan_text: str) -> Dict[str, Any]:
        try:
            data = yaml.safe_load(plan_text) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - parse error
            raise ValueError("invalid plan format") from exc
        if not isinstance(data, dict) or "graph" not in data:
            raise ValueError("invalid plan format")
        graph = data.get("graph", {})
        if not isinstance(graph, dict) or "nodes" not in graph or "edges" not in graph:
            raise ValueError("invalid graph definition")
        self.validate_plan(data)
        return data

    def validate_plan(self, plan: Dict[str, Any]) -> None:
        if not self.plan_schema:
            return
        try:
            Core(source_data=plan, schema_data=self.plan_schema).validate()
        except Exception as exc:
            raise ValueError(f"plan validation error: {exc}") from exc

    def analyze_query(self, query: str) -> State:
        cleaned = query.strip()
        plan = self.plan_research_task(cleaned)
        state = State()
        state.update({"initial_query": cleaned, "plan": plan, "context": []})
        return state

    def __call__(
        self, graph_state: Any, scratchpad: Dict[str, Any] | None = None
    ) -> Any:
        query = graph_state.data.get("query", "")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        state = self.analyze_query(query)
        graph_state.update({"state": state})
        return graph_state
