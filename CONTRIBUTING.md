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

### Codex Task Queue Execution

To run queued tasks locally:

1. Ensure `.codex/queue.yml` is populated.
2. Run `python scripts/codex_queue_runner.py` to execute tasks sequentially.
3. Use `.codex/ticket_template.md` to scaffold new change request tickets.
