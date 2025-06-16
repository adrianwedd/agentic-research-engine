from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict, Iterable, List

from googletrans import Translator


class BackTranslationPipeline:
    """Generate linguistic perturbations via round-trip translation."""

    def __init__(self, pivot_lang: str = "de") -> None:
        self.translator = Translator()
        self.pivot_lang = pivot_lang

    def _back_translate(self, text: str) -> str:
        inter = self.translator.translate(text, dest=self.pivot_lang)
        if asyncio.iscoroutine(inter):
            inter = asyncio.get_event_loop().run_until_complete(inter)
        inter_text = inter.text
        out = self.translator.translate(inter_text, src=self.pivot_lang, dest="en")
        if asyncio.iscoroutine(out):
            out = asyncio.get_event_loop().run_until_complete(out)
        return out.text

    def augment_records(
        self, records: Iterable[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        augmented = []
        for rec in records:
            original = (
                rec.get("corrected_solution") or rec.get("text") or rec.get("original")
            )
            if not original:
                raise ValueError("Record missing 'corrected_solution' field")
            bt = self._back_translate(original)
            augmented.append(
                {
                    "flawed_output": bt,
                    "critique": "",
                    "corrected_solution": original,
                }
            )
        return augmented

    def augment_file(self, input_path: str | Path, output_path: str | Path) -> None:
        records = self._load_records(Path(input_path))
        augmented = self.augment_records(records)
        self._save_records(augmented, Path(output_path))

    @staticmethod
    def _load_records(path: Path) -> List[Dict[str, str]]:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        if text[0] == "[":
            return json.loads(text)
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    @staticmethod
    def _save_records(records: List[Dict[str, str]], path: Path) -> None:
        with path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
