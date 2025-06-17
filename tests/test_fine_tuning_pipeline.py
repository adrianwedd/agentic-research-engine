import time
from pathlib import Path

from pipelines.fine_tuning import MultiAgentFinetunePipeline


def test_multi_agent_finetune_parallel(monkeypatch, tmp_path):
    calls = []

    class FakeTrainer:
        def __init__(
            self, data_path, reward_model_path, model_name="", out_dir=Path(".")
        ):
            self.data_path = Path(data_path)
            self.out_dir = Path(out_dir)

        def run(self, epochs: int = 1):
            calls.append(self.data_path.name)
            time.sleep(0.1)
            return {"average_reward": 1.0}

    dataset_map = {}
    for i in range(5):
        data = tmp_path / f"agent{i}.json"
        data.write_text("[]", encoding="utf-8")
        dataset_map[f"agent{i}"] = data

    reward_file = tmp_path / "reward.json"
    reward_file.write_text("{}", encoding="utf-8")

    pipeline = MultiAgentFinetunePipeline(
        dataset_map, reward_file, trainer_cls=FakeTrainer, out_root=tmp_path
    )
    start = time.perf_counter()
    metrics = pipeline.run(epochs=1, max_workers=5)
    duration = time.perf_counter() - start

    assert set(calls) == {f"agent{i}.json" for i in range(5)}
    assert set(metrics.keys()) == {f"agent{i}" for i in range(5)}
    # parallel execution should be faster than sequential (0.5s)
    assert duration < 0.5
