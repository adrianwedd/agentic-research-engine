from __future__ import annotations

"""Simple two-level Feudal Network implementation."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Protocol

from agents.memory_manager import MemoryManagerAgent
from services.ltm_service.skill_library import SkillLibrary


class Env(Protocol):
    """Minimal environment interface used by ``Worker``."""

    state: Any
    goal: Any

    def reset(self) -> Any:
        ...

    def step(self, action: Any) -> tuple[Any, float, bool, Dict[str, Any]]:
        ...


@dataclass
class Worker:
    """Execute skills conditioned on manager goals."""

    env: Env

    def execute(self, skill: Dict[str, Any], *, goal: Any) -> List[Dict[str, Any]]:
        """Run ``skill`` in ``env`` and return a trajectory."""

        actions: Iterable[Any] = skill.get("actions", [])
        trajectory: List[Dict[str, Any]] = []
        for act in actions:
            state, ext_reward, done, info = self.env.step(act)
            intrinsic = -abs(goal - state) if isinstance(state, (int, float)) else 0.0
            trajectory.append(
                {
                    "state": state,
                    "action": act,
                    "reward": ext_reward,
                    "intrinsic_reward": intrinsic,
                    "info": info,
                }
            )
            if done:
                break
        return trajectory


@dataclass
class Manager:
    """High-level controller selecting skills for the Worker."""

    skill_library: SkillLibrary
    worker: Worker
    memory_manager: MemoryManagerAgent | None = None
    goal_embedding_text: str = field(default="")

    def _select_skill(self, goal_text: str) -> Dict[str, Any] | None:
        results = self.skill_library.query_by_vector(goal_text, limit=1)
        return results[0] if results else None

    def act(self, goal_text: str) -> List[Dict[str, Any]]:
        """Execute a skill matching ``goal_text`` and log the outcome."""

        skill = self._select_skill(goal_text)
        if not skill:
            return []
        self.goal_embedding_text = goal_text
        trajectory = self.worker.execute(
            skill["skill_policy"], goal=self.worker.env.goal
        )
        record = {
            "task_context": {"goal": goal_text, "skill_id": skill["id"]},
            "execution_trace": {"trajectory": trajectory},
            "outcome": {"final_state": self.worker.env.state},
        }
        if self.memory_manager:
            self.memory_manager.tool_registry.invoke(
                "MemoryManager",
                "consolidate_memory",
                record,
                endpoint=self.memory_manager.endpoint,
            )
            proc_record = {
                "task_context": {"goal": goal_text},
                "procedure": skill["skill_policy"].get("actions", []),
                "outcome": {"final_state": self.worker.env.state},
            }
            self.memory_manager.tool_registry.invoke(
                "MemoryManager",
                "consolidate_memory",
                {"record": proc_record, "memory_type": "procedural"},
                endpoint=self.memory_manager.endpoint,
            )
        return trajectory
