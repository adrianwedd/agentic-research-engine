from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

PREFERENCE_LOG = Path("data/preferences.jsonl")


def log_preference(pref: Dict[str, Any], path: str | Path = PREFERENCE_LOG) -> None:
    """Append a preference record to ``path`` as JSONL."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(pref) + "\n")
