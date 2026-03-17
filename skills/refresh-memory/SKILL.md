---
name: refresh-memory
description: Refresh repo and directory memory after a task changes durable knowledge.
---

# Refresh Memory

Use this skill after implementation and review evidence are in place.

## Goals

- keep `SUMMARY.md` accurate
- keep touched `DIRECTORY.md` files current
- create missing directory guides from `.harness/templates/directory.md`

## Rules

- update only durable knowledge, not runtime state
- refresh the nearest `DIRECTORY.md` for changed directories when local behavior changed
- keep `README.md` and `REQUIREMENT.md` aligned when setup or constraints changed
- note unchanged docs explicitly in the final report when they were considered

## Output

Apply the smallest durable documentation update that keeps future readers and agents unblocked.
