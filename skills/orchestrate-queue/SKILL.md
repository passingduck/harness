---
name: orchestrate-queue
description: Create and maintain phase-1 queue items, review stages, and task ownership from an approved plan.
---

# Orchestrate Queue

Use this skill after a spec and implementation plan are approved and ready to become executable queue work.

## Goals

- turn approved plan sections into deterministic queue items under `.harness/runtime/queue/`
- preserve full task schema expectations from `.harness/templates/task.md`
- generate enough metadata for `claim-task` to produce a useful context pack
- keep status handling and ownership explicit from backlog through done

## Rules

- start from `.harness/templates/task.md`; do not invent a parallel schema
- write tasks into `.harness/runtime/queue/<state>/task-id.md`
- the queue directory name is authoritative for state
- queue frontmatter `status` must mirror the directory name exactly
- keep `worktree: null` until `claim-task` moves the item into `in_progress`
- use `.harness/policies/review-stages.yaml` for stage names, verdicts, and handoff expectations
- include the full queue contract:
  - `id`, `title`, `status`, `priority`, `owner_role`, `model_hint`, `worktree`
  - `parent_spec`, `parent_plan`, `why_this_task_exists`
  - `owned_paths`, `required_reads`, `disallowed_edits`, `docs_to_update`, `constraints`
  - `verification_commands`, `expected_report_schema`, `review_stages`, `dependencies`
- make `owned_paths` and `disallowed_edits` precise enough that an implementer can stay inside scope without guessing
- split approved plans into small, independently claimable tasks instead of one broad omnibus task

## Workflow

1. Read the approved plan and isolate one implementation outcome per queue item.
2. Fill the queue schema completely, especially `why_this_task_exists`, `owned_paths`, `verification_commands`, and `expected_report_schema`.
3. Place new work in `backlog` or `ready` based on dependency state.
4. Keep dependencies explicit so promotion from `backlog` to `ready` is deterministic.
5. When a worker runs `claim-task`, expect the tool to:
   - move the task into `.harness/runtime/queue/in_progress/`
   - rewrite frontmatter `status: in_progress`
   - set `worktree` to the claimed task id
   - generate a context pack under `.harness/runtime/context-packs/`
6. Treat that context pack as a projection of the task contract, not a place to invent new scope.

## Context Pack Expectations

- `claim-task` should surface the durable task narrative and the fields implementers need to work safely
- include the problem statement, why the task exists, scope boundaries, required reads, constraints, and verification commands
- if the queue item is underspecified, fix the queue item first; do not rely on ad hoc context outside the task file

## Output

Write concise, deterministic queue items using `.harness/templates/task.md` as the source template. Prefer clarity over prose volume, but never omit required schema fields.
