---
name: refresh-memory
description: Refresh repo and directory memory after a task changes durable knowledge.
---

# Refresh Memory

Use this skill when a completed change altered durable repository knowledge and the local docs need to stay useful for the next worker.

## Goals

- keep `SUMMARY.md` accurate
- keep touched `DIRECTORY.md` files current
- create missing directory guides from `.harness/templates/directory.md`

## Rules

- update only durable knowledge, not runtime state
- refresh the nearest `DIRECTORY.md` for changed directories when local behavior, ownership, interfaces, invariants, or gotchas changed
- keep `README.md` and `REQUIREMENT.md` aligned when setup or constraints changed
- use `scripts/harness/refresh-memory.sh --changed-path <relpath>` to generate missing directory-guide drafts before writing semantic content
- the generated draft is only a scaffold; you must fill in real purpose, interfaces, dependencies, invariants, and update triggers
- if a `DIRECTORY.md` already exists, treat the script output as a pointer to review that guide, not permission to overwrite good content
- update `DIRECTORY.md` when:
  - a directory gained a new responsibility
  - public interfaces or commands changed
  - important domain knowledge or invariants changed
  - recurring failure modes or integration gotchas were discovered
- do not update `DIRECTORY.md` for incidental refactors with no durable knowledge change
- note unchanged docs explicitly in the final report when they were considered

## Workflow

1. Identify the changed paths that carry durable knowledge.
2. Run `scripts/harness/refresh-memory.sh` with one `--changed-path` per affected path.
3. Open each returned `DIRECTORY.md`.
4. Fill the draft using the current code and review evidence:
   - `Directory Purpose`: what this directory owns now
   - `Owned Paths` and `Public Interfaces`: real files, commands, or APIs
   - `Domain Knowledge` and `Invariants And Gotchas`: durable semantics, not task notes
   - `Change Checklist` and `Update Triggers`: when future workers must revisit this guide
5. Recheck `SUMMARY.md`, `README.md`, and `REQUIREMENT.md` for related durable changes.

## Output

Apply the smallest durable documentation update that keeps future readers and agents unblocked.
