from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List

from tenacity import retry, stop_after_attempt, wait_exponential


class TeacherDataPipeline:
    """Generate synthetic self-correction examples using a teacher LLM."""

    def __init__(self, llm: Callable[[str], str], out_dir: str | Path = "data/teacher_dataset") -> None:
        self.llm = llm
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _build_prompt(self, topic: str) -> str:
        return (
            "You are a knowledgeable instructor. "
            "Given the following topic, act like a typical student who makes a reasoning mistake. "
            "Provide a JSON object with fields: original_problem, flawed_output, detailed_critique, corrected_solution. "
            "Topic: "
            + topic
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _call_llm(self, prompt: str) -> str:
        return self.llm(prompt)

    def generate_example(self, topic: str) -> Dict[str, str]:
        prompt = self._build_prompt(topic)
        response = self._call_llm(prompt)
        data = json.loads(str(response))
        required = ["original_problem", "flawed_output", "detailed_critique", "corrected_solution"]
        if not all(key in data for key in required):
            raise ValueError("Missing required fields in LLM response")
        return data

    def run(self, topics: List[str], out_file: str | Path | None = None) -> List[Dict[str, str]]:
        results = []
        for topic in topics:
            try:
                results.append(self.generate_example(topic))
            except Exception:
                continue
        if out_file:
            Path(out_file).write_text(json.dumps(results, indent=2), encoding="utf-8")
        return results
