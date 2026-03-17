---
name: orchestrate-queue
description: Create and maintain phase-1 queue items, review stages, and task ownership from an approved plan.
---

# Orchestrate Queue

Use this skill to turn an approved plan into queue items under `.harness/runtime/queue/`.

## Goals

- keep queue metadata deterministic
- assign explicit ownership and review stages
- preserve the queue state machine

## Rules

- the queue directory name is authoritative for state
- queue frontmatter `status` must mirror the directory name
- include `why_this_task_exists`, `owned_paths`, `disallowed_edits`, `constraints`, `verification_commands`, and `expected_report_schema`
- keep `worktree: null` until a task is claimed
- use `.harness/policies/review-stages.yaml` for stage names and verdict contracts

## Output

Write concise queue items using `.harness/templates/task.md` as the source template.
