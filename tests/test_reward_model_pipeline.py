import json

from pipelines.reward_model import (
    CompositeRewardConfig,
    CompositeRewardFunction,
    LinearPreferenceModel,
    RewardModelTrainer,
)


def test_reward_model_training(tmp_path):
    records = [
        {"trace": "step1 step2", "score": 1.0},
        {"trace": "step1 step2 step3 step4", "score": 2.0},
        {"trace": "short", "score": 0.5},
    ]
    data_file = tmp_path / "traces.json"
    data_file.write_text(json.dumps(records), encoding="utf-8")
    out_dir = tmp_path / "model"

    trainer = RewardModelTrainer(data_file, out_dir)
    reward_fn = trainer.run()
    assert isinstance(reward_fn, CompositeRewardFunction)
    model_file = out_dir / "preference_model.json"
    assert model_file.is_file()
    model = json.loads(model_file.read_text())
    assert "a" in model and "b" in model
    reward = reward_fn("p", "bad", "good answer")
    assert isinstance(reward, float)


def test_composite_reward_meaningful_vs_trivial(tmp_path):
    pref_path = tmp_path / "pref.json"
    pref_path.write_text(json.dumps({"a": 0.0, "b": 0.0}), encoding="utf-8")
    pref_model = LinearPreferenceModel.from_file(pref_path)
    reward_fn = CompositeRewardFunction(
        pref_model,
        config=CompositeRewardConfig(w_cost=0.0, tau_fail=0.1, tau_pass=-0.1),
    )
    high = reward_fn("p", "wrong answer", "correct and different answer")
    low = reward_fn("p", "a", "a")
    assert high > low
