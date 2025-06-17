import random
from typing import Dict, List, Tuple

from services.learning.skill_discovery import SkillDiscoveryModule
from services.ltm_service.skill_library import SkillLibrary


class DummyEnv:
    def __init__(self) -> None:
        self.state = [0.0, 0.0]

    def reset(self) -> List[float]:
        self.state = [0.0, 0.0]
        return self.state

    def step(self, action: List[float]) -> Tuple[List[float], float, bool, Dict]:
        self.state = [s + a for s, a in zip(self.state, action)]
        return self.state, 0.0, False, {}

    def sample_action(self, skill_vector: List[float] | None = None) -> List[float]:
        return [random.uniform(-1, 1) for _ in range(2)]

    def get_state_embedding(self, state: List[float]) -> List[float]:
        return list(state)


def test_skill_discovery_basic():
    env = DummyEnv()
    library = SkillLibrary()
    module = SkillDiscoveryModule(env, library=library)
    data = module.collect_exploration_data(steps=5)
    ids = module.learn_skills(data)
    assert len(ids) == 5
    metrics = module.evaluate()
    assert "diversity" in metrics and "disentanglement" in metrics
