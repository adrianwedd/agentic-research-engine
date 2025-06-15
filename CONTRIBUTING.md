# Contributing Guidelines

Thank you for helping improve this project!

### Codex Task Queue

To define or extend automated Codex tasks:

1. Edit `.codex/queue.yml`—ensure each entry has `id`, `priority`, `retry_policy`, and `timeout`.
2. Run `python scripts/codex_task_runner.py` to validate your queue.
3. Use `.codex/ticket_template.md` to scaffold new change request tickets.
4. Submit your PR; CI will lint `.codex/queue.yml` and fail on schema errors.
