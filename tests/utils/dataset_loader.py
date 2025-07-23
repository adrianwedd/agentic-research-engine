import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def load_dataset(path: str | Path) -> List[Dict[str, Any]]:
    """Load evaluation dataset from ``path``.

    Supports JSON and CSV files. Returns a list of dict records.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    if p.suffix == ".json":
        text = p.read_text(encoding="utf-8")
        data = json.loads(text or "[]")
        if not isinstance(data, list):
            raise ValueError("JSON dataset must be a list of objects")
        return data
    if p.suffix == ".csv":
        with p.open(newline="", encoding="utf-8") as f:
            return [dict(row) for row in csv.DictReader(f)]
    raise ValueError(f"Unsupported dataset format: {p.suffix}")
