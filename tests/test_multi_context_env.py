from services.learning import MultiContextEnv
from services.learning.skill_discovery import SkillDiscoveryModule  # noqa: F401
from services.ltm_service.skill_library import SkillLibrary  # noqa: F401


class DummyEnv:
    def __init__(self, start=0):
        self.start = start
        self.state = [float(start), 0.0]

    def reset(self):
        self.state = [float(self.start), 0.0]
        return self.state

    def step(self, action):
        self.state = [s + a for s, a in zip(self.state, action)]
        return self.state, 0.0, False, {}

    def sample_action(self, skill_vector=None):
        return [0.0, 0.0]

    def get_state_embedding(self, state):
        return list(state)


def test_multi_context_env_cycles():
    envs = [DummyEnv(0), DummyEnv(5)]
    m = MultiContextEnv(envs)
    s1 = m.reset()
    assert s1 == [0.0, 0.0]
    s2 = m.reset()
    assert s2 == [5.0, 0.0]
    s3 = m.reset()
    assert s3 == [0.0, 0.0]
