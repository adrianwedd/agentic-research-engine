from __future__ import annotations

"""Unsupervised skill discovery using a simplified DUSDi-style algorithm."""

import logging
from typing import Any, Dict, Iterable, List, Protocol, Tuple

from services.ltm_service.skill_library import SkillLibrary


class ExplorationEnv(Protocol):
    """Minimal environment interface for exploration."""

    def reset(self) -> Any:
        """Reset environment and return initial state."""

    def step(self, action: Any) -> Tuple[Any, float, bool, Dict]:
        """Advance environment with ``action`` and return (state, reward, done, info)."""

    def sample_action(self, skill_vector: List[float] | None = None) -> Any:
        """Sample an exploratory action optionally conditioned on ``skill_vector``."""

    def get_state_embedding(self, state: Any) -> List[float]:
        """Return vector embedding of ``state`` for skill learning."""


class SkillDiscoveryModule:
    """Discover skills via reward-free exploration and store them in :class:`SkillLibrary`."""

    def __init__(
        self,
        env: ExplorationEnv,
        *,
        skill_dim: int = 8,
        library: SkillLibrary | None = None,
    ) -> None:
        self.env = env
        self.skill_dim = skill_dim
        self.library = library or SkillLibrary()
        self.logger = logging.getLogger(__name__)

    # --------------------------------------------------------------
    # Exploration
    # --------------------------------------------------------------
    def collect_exploration_data(
        self, steps: int = 100
    ) -> List[Dict[str, List[float]]]:
        """Roll out the environment and return state transition embeddings."""

        data: List[Dict[str, List[float]]] = []
        state = self.env.reset()
        for _ in range(steps):
            action = self.env.sample_action()
            next_state, _reward, done, _info = self.env.step(action)
            data.append(
                {
                    "state": self.env.get_state_embedding(state),
                    "next_state": self.env.get_state_embedding(next_state),
                }
            )
            if done:
                state = self.env.reset()
            else:
                state = next_state
        return data

    # --------------------------------------------------------------
    # Skill learning
    # --------------------------------------------------------------
    def _mutual_information(
        self, skills: List[List[float]], states: List[List[float]]
    ) -> float:
        """Return a toy mutual information estimate between skills and states."""

        if not skills or not states:
            return 0.0
        # Use a simple proxy based on pairwise distances
        diversity = 0.0
        count = 0
        for s in skills:
            for t in states:
                diversity += sum((a - b) ** 2 for a, b in zip(s, t)) ** 0.5
                count += 1
        return diversity / float(count)

    def learn_skills(self, data: Iterable[Dict[str, List[float]]]) -> List[str]:
        """Convert transitions into skills and store them in the :class:`SkillLibrary`."""

        skill_ids: List[str] = []
        skills: List[List[float]] = []
        states: List[List[float]] = []
        for rec in data:
            state = rec["state"]
            next_state = rec["next_state"]
            diff = [b - a for a, b in zip(state, next_state)]
            skills.append(diff)
            states.append(next_state)
            skill_id = self.library.add_skill(
                {"delta": diff},
                diff,
                {"source": "url"},
            )
            skill_ids.append(skill_id)
        mi = self._mutual_information(skills, states)
        self.logger.info("Estimated MI: %s", mi)
        return skill_ids

    # --------------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------------
    def evaluate(self) -> Dict[str, float]:
        """Return simple diversity and disentanglement metrics."""

        embeddings = [rec["skill_representation"] for rec in self.library.all_skills()]
        n = len(embeddings)
        if n < 2:
            return {"diversity": 0.0, "disentanglement": 0.0}
        # diversity as average pairwise distance
        div = 0.0
        cnt = 0
        for i in range(n):
            for j in range(i + 1, n):
                div += (
                    sum((a - b) ** 2 for a, b in zip(embeddings[i], embeddings[j]))
                    ** 0.5
                )
                cnt += 1
        diversity = div / float(cnt)
        # disentanglement as average absolute correlation between dims
        dims = len(embeddings[0])
        disent = 0.0
        for d in range(dims):
            vals = [e[d] for e in embeddings]
            mean = sum(vals) / n
            var = sum((v - mean) ** 2 for v in vals) / n
            if var == 0:
                continue
            for other in range(d + 1, dims):
                vals2 = [e[other] for e in embeddings]
                mean2 = sum(vals2) / n
                cov = sum((v - mean) * (w - mean2) for v, w in zip(vals, vals2)) / n
                var2 = sum((w - mean2) ** 2 for w in vals2) / n
                if var2:
                    corr = cov / ((var * var2) ** 0.5)
                    disent += abs(corr)
        pairs = dims * (dims - 1) / 2
        disentanglement = 1.0 - disent / pairs if pairs else 0.0
        metrics = {"diversity": diversity, "disentanglement": disentanglement}
        self.logger.info("Skill metrics: %s", metrics)
        return metrics
