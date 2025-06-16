#!/usr/bin/env python3
"""Fail CI if training configs lack a guidance_loss block."""

import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback if PyYAML missing
    yaml = None


def load_config(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("PyYAML required for YAML config parsing")
        return yaml.safe_load(text) or {}
    if path.suffix == ".json":
        return json.loads(text or "{}")
    return {}


def main() -> int:
    base = Path("configs/training")
    if not base.exists():
        return 0
    missing = []
    for file in base.rglob("*"):
        if file.suffix not in {".yml", ".yaml", ".json"}:
            continue
        data = load_config(file)
        if "guidance_loss" not in data:
            missing.append(str(file))
    if missing:
        print(
            "Configuration files missing guidance_loss (see ADR-003):", file=sys.stderr
        )
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
