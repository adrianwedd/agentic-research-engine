import pytest

from services.learning.rlaif_system import RLAIFSystem


class DummyRewardModel:
    def score(self, experience):
        return experience.get("quality", 0)


class DummyPolicyOptimizer:
    def __init__(self):
        self.updates = []

    def update(self, experience, reward):
        self.updates.append((experience, reward))
        # return a mock loss value proportional to negative reward
        return -reward


class DummyCompositeReward:
    def __init__(self):
        self.calls = []

    def __call__(self, prompt, out1, out2):
        self.calls.append((prompt, out1, out2))
        return float(len(out2) - len(out1))


def test_update_agent_policies():
    rlaif = RLAIFSystem(DummyRewardModel(), DummyPolicyOptimizer())
    batch = [{"quality": 1.0}, {"quality": 0.5}]
    metrics = rlaif.update_agent_policies(batch)
    assert metrics["average_reward"] == 0.75
    assert metrics["average_loss"] == -0.75
    # replay_buffer should contain the experiences
    assert len(rlaif.replay_buffer) == 2


def test_rlaif_with_ppo(tmp_path):
    _ = pytest.importorskip("trl")
    from services.learning.ppo_policy_optimizer import PPOPolicyOptimizer

    reward_model = DummyRewardModel()
    optimizer = PPOPolicyOptimizer("sshleifer/tiny-gpt2", log_dir=tmp_path)
    rlaif = RLAIFSystem(reward_model, optimizer)
    batch = [{"prompt": "hi", "response": " there", "quality": 1.0}]
    metrics = rlaif.update_agent_policies(batch)
    assert "average_reward" in metrics
    assert (tmp_path / "policy" / "config.json").exists()


def test_composite_reward_integration():
    reward_model = DummyCompositeReward()
    optimizer = DummyPolicyOptimizer()
    rlaif = RLAIFSystem(reward_model, optimizer)
    traj = {
        "original_problem": "Q",
        "flawed_output": "bad",
        "corrected_solution": "good answer",
    }
    expected_reward = len("good answer") - len("bad")
    metrics = rlaif.update_agent_policies([traj])
    assert metrics["average_reward"] == expected_reward
    assert reward_model.calls == [("Q", "bad", "good answer")]
    assert optimizer.updates == [(traj, expected_reward)]
