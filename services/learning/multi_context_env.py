from __future__ import annotations

"""Environment wrapper cycling through multiple contexts."""

from typing import List

from .skill_discovery import ExplorationEnv


class MultiContextEnv:
    """Combine several `ExplorationEnv` instances for diverse training."""

    def __init__(self, envs: List[ExplorationEnv]):
        if not envs:
            raise ValueError("envs list cannot be empty")
        self._envs = list(envs)
        self._index = -1
        self._cur = self._envs[0]

    def _next_env(self) -> ExplorationEnv:
        self._index = (self._index + 1) % len(self._envs)
        self._cur = self._envs[self._index]
        return self._cur

    # expose goal attribute of current env
    @property
    def goal(self):
        return getattr(self._cur, "goal", None)

    @goal.setter
    def goal(self, value):
        if hasattr(self._cur, "goal"):
            setattr(self._cur, "goal", value)

    # The following methods proxy to the current env
    def reset(self):
        self._next_env()
        return self._cur.reset()

    def step(self, action):
        return self._cur.step(action)

    def sample_action(self, skill_vector=None):
        return self._cur.sample_action(skill_vector)

    def get_state_embedding(self, state):
        return self._cur.get_state_embedding(state)
