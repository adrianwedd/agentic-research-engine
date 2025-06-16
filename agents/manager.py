from __future__ import annotations

"""Simple Manager agent that delegates tasks to worker agents."""

import asyncio
from typing import Any, Callable, Dict, List

from engine.orchestration_engine import GraphState, create_orchestration_engine
from engine.state import State


class ManagerAgent:
    """Plan tasks and delegate to specialized worker agents."""

    def __init__(
        self,
        web_researcher: Callable[[List[Dict[str, Any]], State, Dict[str, Any]], Any],
        code_researcher: Callable[[List[Dict[str, Any]], State, Dict[str, Any]], Any],
    ) -> None:
        self.web_researcher = web_researcher
        self.code_researcher = code_researcher

    def _plan(self, query: str) -> Dict[str, Any]:
        """Generate a very simple plan for demo purposes."""
        return {
            "query": query,
            "graph": {
                "nodes": [
                    {"id": "web", "agent": "WebResearcher", "task": query},
                    {"id": "code", "agent": "CodeResearcher", "task": query},
                ],
                "edges": [{"from": "web", "to": "code"}],
            },
        }

    def _wrap_agent(self, agent: Callable, name: str):
        def node(state: GraphState, _: Dict[str, Any]) -> GraphState:
            result = agent([], state, state.scratchpad)
            if isinstance(result, dict):
                content = result.get("content", "")
            else:
                content = str(result)
            state.add_message({"sender": name, "content": content})
            return state

        return node

    async def run_async(self, query: str) -> GraphState:
        plan = self._plan(query)
        state = GraphState(data={"query": query, "plan": plan})
        engine = create_orchestration_engine()

        def plan_node(state: GraphState, _: Dict[str, Any]) -> GraphState:
            state.add_message({"sender": "Manager", "content": "plan created"})
            return state

        engine.add_node("Plan", plan_node)
        engine.add_node("web", self._wrap_agent(self.web_researcher, "WebResearcher"))
        engine.add_node(
            "code", self._wrap_agent(self.code_researcher, "CodeResearcher")
        )
        engine.add_edge("Plan", "web")
        engine.add_edge("web", "code")
        engine.build()
        result = await engine.run_async(state, thread_id="manager")
        return result

    def run(self, query: str) -> GraphState:
        return asyncio.run(self.run_async(query))
