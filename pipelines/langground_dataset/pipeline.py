from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple


class CommunicationDatasetPipeline:
    """Generate (observation, action) -> natural language message pairs."""

    def __init__(
        self, llm: Callable[[str], str], out_dir: str | Path = "data/comms_dataset"
    ) -> None:
        self.llm = llm
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _build_prompt(self, obs: str, act: str) -> str:
        return f"Observation: {obs}\nAction: {act}\nDescribe this state in natural language."

    def generate_record(self, obs: str, act: str) -> Dict[str, str]:
        prompt = self._build_prompt(obs, act)
        message = self.llm(prompt)
        return {"observation": obs, "action": act, "message": str(message)}

    def run(
        self, pairs: Iterable[Tuple[str, str]], out_file: str | Path | None = None
    ) -> List[Dict[str, str]]:
        records = [self.generate_record(o, a) for o, a in pairs]
        if out_file:
            Path(out_file).write_text(json.dumps(records, indent=2), encoding="utf-8")
        return records
