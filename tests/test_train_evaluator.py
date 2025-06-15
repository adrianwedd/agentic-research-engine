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
