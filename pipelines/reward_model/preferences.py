from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .pipeline import RewardModelTrainer


def preferences_to_records(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        prefs = json.loads(text)
    else:
        prefs = [json.loads(line) for line in text.splitlines() if line.strip()]

    records: List[Dict[str, Any]] = []
    for pref in prefs:
        better = pref.get("better") or pref.get("preferred")
        worse = pref.get("worse") or pref.get("other")
        if better is not None:
            records.append({"trace": better, "score": 1.0})
        if worse is not None:
            records.append({"trace": worse, "score": 0.0})
    return records


def train_from_preferences(pref_path: str | Path, out_dir: str | Path) -> RewardModelTrainer:
    """Train a reward model using logged preference pairs."""
    records = preferences_to_records(pref_path)
    temp = Path(out_dir) / "_prefs.jsonl"
    temp.parent.mkdir(parents=True, exist_ok=True)
    with temp.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    trainer = RewardModelTrainer(temp, out_dir)
    trainer.run()
    temp.unlink()
    return trainer
