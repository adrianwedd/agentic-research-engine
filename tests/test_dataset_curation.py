import json
import re

import pytest

from scripts import dataset_curation

pytestmark = pytest.mark.core


def test_validation_flags_and_quarantines(tmp_path):
    records = [
        {
            "original_text": "a",
            "erroneous_version": "b",
            "critique": "c",
            "corrected_version": "d",
        },
        {
            "original_text": "a",
            "erroneous_version": "a",
            "corrected_version": "a",
        },
    ]
    valid, invalid = dataset_curation.validate_records(records)
    assert len(valid) == 1
    assert len(invalid) == 1
    assert any("missing critique" in e for e in invalid[0]["_errors"])


def test_versioning_creates_output(tmp_path):
    records = [
        {
            "original_text": "a",
            "erroneous_version": "b",
            "critique": "c",
            "corrected_version": "d",
        }
    ]
    version = dataset_curation.save_version(records, tmp_path)
    out_file = tmp_path / version / "dataset.json"
    assert out_file.is_file()
    loaded = json.loads(out_file.read_text())
    assert loaded == records


def test_version_id_format(tmp_path):
    version = dataset_curation.save_version([], tmp_path)
    assert re.match(r"^\d{8}_\d{6}$", version)
    out_file = tmp_path / version / "dataset.json"
    assert out_file.is_file()
