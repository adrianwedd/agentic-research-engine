import json

from scripts import train_evaluator


def test_prepare_datasets(tmp_path):
    records = [
        {"erroneous_version": "Helo world", "corrected_version": "Hello world"},
        {"erroneous_version": "Gbye", "corrected_version": "Goodbye"},
    ]
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(records), encoding="utf-8")
    train_ds, eval_ds = train_evaluator.prepare_datasets(data_file, test_split=0.5)
    assert len(train_ds) + len(eval_ds) == 2
    assert all("input" in ex and "label" in ex for ex in train_ds)


def test_metrics_file_created(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    data_file.write_text("[]", encoding="utf-8")

    out_root = tmp_path / "models"
    baseline_trainer = object()
    finetuned_trainer = object()

    def fake_build_trainer(*args, **kwargs):
        return baseline_trainer

    def fake_train_model(*args, **kwargs):
        # emulate side effect of creating output directory
        out_dir = kwargs.get("out_dir") or args[3]
        (out_dir).mkdir(parents=True, exist_ok=True)
        return finetuned_trainer

    def fake_evaluate_model(trainer, _):
        if trainer is baseline_trainer:
            return 0.5
        return 0.75

    monkeypatch.setattr(train_evaluator, "build_trainer", fake_build_trainer)
    monkeypatch.setattr(train_evaluator, "train_model", fake_train_model)
    monkeypatch.setattr(train_evaluator, "evaluate_model", fake_evaluate_model)

    args = [
        "--data-path",
        str(data_file),
        "--model",
        "dummy",
        "--epochs",
        "1",
        "--out-root",
        str(out_root),
        "--version",
        "v1",
    ]
    monkeypatch.setattr("sys.argv", ["train_evaluator.py", *args])
    train_evaluator.main()

    metrics = json.loads((out_root / "v1" / "metrics.json").read_text())
    assert metrics["baseline_model_accuracy"] == 0.5
    assert metrics["finetuned_model_accuracy"] == 0.75
