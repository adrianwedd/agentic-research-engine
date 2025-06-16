"""Script to generate a synthetic communication dataset using an LLM."""

from __future__ import annotations

import json
from pathlib import Path

import openai

from pipelines.langground_dataset import CommunicationDatasetPipeline


def openai_llm(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message["content"]


def main() -> None:
    pairs_path = Path("data/observation_action_pairs.json")
    pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
    pipeline = CommunicationDatasetPipeline(openai_llm)
    records = pipeline.run([(p["observation"], p["action"]) for p in pairs])
    out_file = Path("data/comms_dataset/generated.json")
    out_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} records to {out_file}")


if __name__ == "__main__":
    main()
