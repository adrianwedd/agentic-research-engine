import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    runner = Path("scripts/codex_task_runner.py")
    queue_file = Path(".codex/queue.yml")

    if not runner.is_file():
        print("codex_task_runner.py not found", file=sys.stderr)
        return 1
    if not queue_file.is_file():
        print(
            ".codex/queue.yml not found. "
            "Please generate it using codex_task_runner.py",
            file=sys.stderr,
        )
        return 1

    root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(root), env.get("PYTHONPATH", "")])

    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        subprocess.run(
            [sys.executable, str(runner), "--preview"],
            check=True,
            stdout=tmp,
            env=env,
        )
        tmp_path = tmp.name

    diff_proc = subprocess.run(["diff", "-u", str(queue_file), tmp_path])
    return diff_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
