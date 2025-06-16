import pytest

from services.learning.ppo_policy_optimizer import PPOPolicyOptimizer


def test_ppo_policy_optimizer_step(tmp_path):
    _ = pytest.importorskip("trl")
    from transformers import AutoTokenizer

    model_name = "sshleifer/tiny-gpt2"
    _ = AutoTokenizer.from_pretrained(model_name)
    optimizer = PPOPolicyOptimizer(model_name, log_dir=tmp_path)
    traj = {"prompt": "Hello", "response": " world"}
    loss = optimizer.update(traj, 1.0)
    assert isinstance(loss, float)
    assert (tmp_path / "policy" / "config.json").exists()
