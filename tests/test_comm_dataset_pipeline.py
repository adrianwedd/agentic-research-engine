import json

from pipelines.langground_dataset import CommunicationDatasetPipeline


def test_dataset_generation(tmp_path):
    def fake_llm(prompt: str) -> str:
        return "message"

    pairs = [(f"obs{i}", f"act{i}") for i in range(1000)]
    out_file = tmp_path / "data.json"
    pipeline = CommunicationDatasetPipeline(fake_llm, out_dir=tmp_path)
    records = pipeline.run(pairs, out_file)
    assert len(records) >= 1000
    saved = json.loads(out_file.read_text())
    assert len(saved) == len(records)
