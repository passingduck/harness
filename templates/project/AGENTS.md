# Mission

Keep this repository markdown-first, repo-native, and deterministic for task execution, review, and memory refresh.

## Instruction Priority

1. Direct human instructions
2. This `AGENTS.md`
3. `.harness/policies/*`
4. Repo docs and templates
5. Tool defaults

## Required Reads

- `README.md`
- `SUMMARY.md`
- `REQUIREMENT.md`
- nearest `DIRECTORY.md`
- task-specific context pack or queue item
- relevant policy files under `.harness/policies/`

## Default Workflow

1. Read the task packet and required docs.
2. Confirm owned paths and disallowed edits.
3. Make the smallest correct change.
4. Refresh required documentation.
5. Run verification and collect evidence.
6. Prepare review output with the required report schema.

## Model Routing Default

Default meaningful-work model: `gpt-5.4`.

Use `gpt-5.1-codex-mini` only for shallow inventory or grep-style indexing work allowed by `.harness/policies/model-routing.yaml`.

## Documentation Gate

Work is not complete until required updates to `README.md`, `SUMMARY.md`, `REQUIREMENT.md`, touched `DIRECTORY.md` files, and any durable review docs are made or explicitly marked as not needed.

## QA Gate

No completion claim, QA pass, or review-ready claim is valid without fresh verification evidence and required review stages.

## Worktree Rule

Tasks that need isolated write access must use `.worktrees/<task-id>`. In phase 1, `worktree_name == task_id`.

## Output Convention

Report with: status, what changed, verification results, files changed, self-review findings, and open concerns.
