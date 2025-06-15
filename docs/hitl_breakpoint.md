# Human-in-the-Loop Breakpoint

A `human_in_the_loop_breakpoint` node pauses graph execution and pushes the
current state to a review queue. Reviewers can inspect the state via a simple
HTTP API and approve or reject the task.

## API Endpoints

- `GET /tasks` – list paused tasks with their serialized state
- `POST /tasks/<id>/approval` – resume execution from the stored point
- `POST /tasks/<id>/rejection` – terminate the task with status `REJECTED_BY_HUMAN`
