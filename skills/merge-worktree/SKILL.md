---
name: merge-worktree
description: Use when a task is already in review and needs optional PR publication plus the final local finish-worktree landing step.
---

# Merge Worktree

## Overview

Use this skill when a task has finished implementation and review receipts now gate the final landing flow. The core rule is simple: `publish-pr` is optional, `finish-worktree` is required, and both must reuse the same task-linked review narrative.

## Before Running Commands

- Confirm the queue item is still in `.harness/runtime/queue/review/`.
- Confirm the required review-result receipts exist under `.harness/runtime/review-results/<task-id>/`.
- Confirm the task-linked PR review narrative exists in runtime drafts or `docs/reviews/`.
- Confirm the target branch you intend to land matches any existing registry `target_branch`.

## Order Of Operations

1. If humans need a GitHub PR before local landing, run `publish-pr` while the task is still in `review`.
2. Reuse the same narrative source path recorded in the registry.
3. Run `finish-worktree` exactly once to perform the local landing and queue finalization.

## Command Reminders

- `scripts/harness/publish-pr.sh --task-id <id> --target-branch <branch>`
- `scripts/harness/finish-worktree.sh --task-id <id> --target-branch <branch>`

## Failure Rules

- Missing review-result receipts block both human-ready claims and `finish-worktree`.
- `publish-pr` is optional and GitHub-specific; do not treat it as the source of truth.
- If `finish-worktree` fails preflight, fix the missing receipt, narrative, or target-branch mismatch before retrying.
