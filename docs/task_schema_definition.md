# Task Schema Definition

This schema is designed to provide a clear and actionable description of each task, making it suitable for use in project management tools or by an automated agent.

```yaml
- task_id: (A unique identifier for the task, e.g., FEAT-001)
  title: (A concise and descriptive title for the task)
  description: (A more detailed explanation of the task and its purpose)
  area: (The functional area of the project the task belongs to, e.g., "Data Analysis", "System Architecture", "Frontend")
  actionable_steps:
    - (A list of specific, actionable steps required to complete the task)
  dependencies:
    - (A list of other task_ids that must be completed before this task can be started)
  acceptance_criteria:
    - (A list of criteria that must be met for the task to be considered complete)
  status: (The current status of the task, e.g., "To Do", "In Progress", "Done")
  assigned_to: (The person or agent responsible for the task)
  epic: (A larger user story or feature that this task is a part of)
```
