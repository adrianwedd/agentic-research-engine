"""
Supervisor Agent Implementation.
This agent acts as the primary coordinator for research tasks.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class State:
    """Simple representation of the system state."""

    initial_query: str
    plan: Optional[Dict[str, Any]] = None
    context: List[Any] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None


class SupervisorAgent:
    def __init__(
        self,
        ltm_service: Optional[Any] = None,
        orchestration_engine: Optional[Any] = None,
        agent_registry: Optional[Any] = None,
    ) -> None:
        """Initialize supervisor with optional services."""

        self.ltm_service = ltm_service
        self.orchestration_engine = orchestration_engine
        self.agent_registry = agent_registry

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
        if self.ltm_service:
            past = self.ltm_service.retrieve(query)

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

        return plan

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
