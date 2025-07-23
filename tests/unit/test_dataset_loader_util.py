import json

import pytest

from tests.utils.dataset_loader import load_dataset


def test_load_json_dataset(tmp_path):
    data = [{"a": 1}, {"a": 2}]
    f = tmp_path / "d.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    loaded = load_dataset(f)
    assert loaded == data


def test_load_csv_dataset(tmp_path):
    csv_text = "a,b\n1,2\n3,4\n"
    f = tmp_path / "d.csv"
    f.write_text(csv_text, encoding="utf-8")
    loaded = load_dataset(f)
    assert loaded == [
        {"a": "1", "b": "2"},
        {"a": "3", "b": "4"},
    ]


def test_unsupported_extension(tmp_path):
    f = tmp_path / "d.txt"
    f.write_text("hi", encoding="utf-8")
    with pytest.raises(ValueError):
        load_dataset(f)
