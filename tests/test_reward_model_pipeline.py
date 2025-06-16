import json

from pipelines.reward_model import RewardModelTrainer


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
    mse = trainer.run()
    assert mse >= 0
    model_file = out_dir / "reward_model.json"
    assert model_file.is_file()
    model = json.loads(model_file.read_text())
    assert "a" in model and "b" in model
