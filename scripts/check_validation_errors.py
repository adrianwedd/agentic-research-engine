import sys
from pathlib import Path


def main(path: str = "tests.log", threshold: int = 5) -> int:
    log = Path(path)
    if not log.is_file():
        print(f"Log not found: {log}", file=sys.stderr)
        return 0
    text = log.read_text()
    count = text.count("InputValidationError")
    if count > threshold:
        print(
            f"Validation errors exceeded threshold: {count} > {threshold}",
            file=sys.stderr,
        )
        return 1
    print(f"Validation errors: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*(sys.argv[1:])))
