import json

import pytest

from pipelines.supervisor_policy import SupervisorPolicyTrainer


def test_supervisor_policy_trainer(tmp_path):
    _ = pytest.importorskip("trl")
    data = [
        {"query": "Q1", "plan": "step a"},
        {"query": "Q2", "plan": "step b step c"},
    ]
    data_file = tmp_path / "traces.json"
    data_file.write_text(json.dumps(data), encoding="utf-8")
    reward_file = tmp_path / "reward_model.json"
    reward_file.write_text(json.dumps({"a": 1.0, "b": 0.0}), encoding="utf-8")
    out_dir = tmp_path / "model"
    trainer = SupervisorPolicyTrainer(
        data_file, reward_file, model_name="sshleifer/tiny-gpt2", out_dir=out_dir
    )
    metrics = trainer.run(epochs=1)
    assert "average_reward" in metrics
    assert (out_dir / "policy" / "config.json").exists()
