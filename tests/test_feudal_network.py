from agents.memory_manager import MemoryManagerAgent
from services.learning.feudal_network import Manager, Worker
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService
from services.ltm_service.skill_library import SkillLibrary
from services.tool_registry import ToolRegistry


class LineEnv:
    def __init__(self, goal: int = 3) -> None:
        self.goal = goal
        self.pos = 0

    @property
    def state(self) -> int:
        return self.pos

    def reset(self) -> int:
        self.pos = 0
        return self.pos

    def step(self, action: int):
        self.pos += action
        done = self.pos >= self.goal
        reward = 1.0 if done else 0.0
        return self.pos, reward, done, {}


def test_feudal_network_memory_update():
    env = LineEnv(goal=2)
    library = SkillLibrary()
    library.add_skill({"actions": [1]}, "forward", {"name": "fwd"})
    library.add_skill({"actions": [-1]}, "backward", {"name": "bwd"})

    worker = Worker(env)
    ltm = LTMService(EpisodicMemoryService(InMemoryStorage()))
    registry = ToolRegistry()

    def store(rec, *, memory_type="episodic", endpoint=None):
        return ltm.consolidate(memory_type, rec)

    registry.register_tool("consolidate_memory", store)
    mm = MemoryManagerAgent(ltm_service=ltm, tool_registry=registry)
    manager = Manager(library, worker, memory_manager=mm)

    env.reset()
    while env.state < env.goal:
        manager.act("forward")

    assert env.state == env.goal
    assert ltm.retrieve("episodic", {})
