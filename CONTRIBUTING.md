# Contributing

Thank you for helping improve this project! The repository uses a generated task queue located at `.codex/queue.yml`. Tasks are defined in `codex_tasks.md` using fenced code blocks tagged `codex-task`.

Example block:

```codex-task
id: CODEX-EXAMPLE-02
title: "Write docs"
priority: medium
steps:
  - draft text
acceptance_criteria:
  - docs committed
```

To regenerate the queue file after editing `codex_tasks.md` run:

```bash
python scripts/codex_task_runner.py
```

Useful flags:

- `--from <ID>` — only rebuild tasks with IDs greater than or equal to `ID`.
- `--preview` — print the resulting YAML to stdout instead of writing to `.codex/queue.yml`.

The CI pipeline verifies that the queue file matches the tasks. Ensure you run the script before opening a pull request.
