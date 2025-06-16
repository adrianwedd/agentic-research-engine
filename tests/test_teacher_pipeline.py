import json

from pipelines.teacher import TeacherDataPipeline


def test_generate_example_valid():
    def fake_llm(prompt: str) -> str:
        return json.dumps(
            {
                "original_problem": "Q",
                "flawed_output": "A",
                "detailed_critique": "factual error",
                "corrected_solution": "C",
            }
        )

    pipeline = TeacherDataPipeline(fake_llm)
    result = pipeline.generate_example("topic")
    assert result["flawed_output"] == "A"


def test_pipeline_diverse_error_types():
    critiques = [
        "factual mistake in reasoning",
        "logical fallacy explanation",
        "omission of key detail",
    ]

    def fake_llm(_prompt: str) -> str:
        text = critiques.pop(0)
        return json.dumps(
            {
                "original_problem": "P",
                "flawed_output": "F",
                "detailed_critique": text,
                "corrected_solution": "C",
            }
        )

    pipeline = TeacherDataPipeline(fake_llm)
    results = pipeline.run(["t1", "t2", "t3"])
    detail_texts = [r["detailed_critique"] for r in results]
    assert any("factual" in d for d in detail_texts)
    assert any("logical" in d for d in detail_texts)
    assert any("omission" in d for d in detail_texts)
