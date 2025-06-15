import json
from pathlib import Path
import os

import openai

from pipelines.teacher import TeacherDataPipeline


def openai_llm(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model=os.getenv("TEACHER_MODEL", "gpt-4"),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message["content"]


def main():
    topics_path = Path("data/topics.txt")
    topics = topics_path.read_text(encoding="utf-8").splitlines()
    pipeline = TeacherDataPipeline(openai_llm)
    results = pipeline.run(topics)
    out_file = Path("data/teacher_dataset/generated.json")
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} examples to {out_file}")


if __name__ == "__main__":
    main()
