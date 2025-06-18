from services.learning import Manager, MultiContextEnv, Worker, evaluate_transfer
from services.ltm_service.skill_library import SkillLibrary  # noqa: F401


class TinyEnv:
    def __init__(self, goal=0):
        self.goal = goal
        self.state = 0

    def reset(self):
        self.state = 0
        return self.state

    def step(self, action):
        self.state += action
        return self.state, 0.0, self.state == self.goal, {}

    def sample_action(self, skill_vector=None):
        return 1

    def get_state_embedding(self, state):
        return [float(state)]


def test_evaluate_transfer():
    envs = [TinyEnv(goal=1), TinyEnv(goal=2)]
    mc = MultiContextEnv(envs)
    worker = Worker(mc)
    lib = SkillLibrary()
    sid = lib.add_skill({"actions": [1]}, "inc")  # noqa: F841
    mgr = Manager(lib, worker)
    tasks = [
        {"goal": 1, "description": "inc"},
        {"goal": 2, "description": "inc, inc"},
    ]
    res = evaluate_transfer(tasks, mgr)
    assert "success_rate" in res
