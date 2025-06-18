import json

from pipelines.back_translation.pipeline import BackTranslationPipeline


class DummyTranslation:
    """Simple object to mimic googletrans translation result."""

    def __init__(self, text: str):
        self.text = text


def test_back_translation_pipeline(monkeypatch, tmp_path):
    input_file = tmp_path / "input.jsonl"
    input_file.write_text(json.dumps({"corrected_solution": "Hello world"}) + "\n")
    output_file = tmp_path / "out.jsonl"

    monkeypatch.setattr(
        BackTranslationPipeline, "_back_translate", lambda self, text: "Hallo Welt"
    )
    pipeline = BackTranslationPipeline(pivot_lang="de")
    pipeline.augment_file(input_file, output_file)

    out_records = [json.loads(line) for line in output_file.read_text().splitlines()]
    assert len(out_records) == 1
    out = out_records[0]
    assert out["corrected_solution"] == "Hello world"
    assert out["flawed_output"] == "Hallo Welt"
    assert "critique" in out
