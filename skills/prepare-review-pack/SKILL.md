---
name: prepare-review-pack
description: Assemble phase-1 evidence and human-readable review packs from completed task work.
---

# Prepare Review Pack

Use this skill when code and documentation changes are ready for review.

## Goals

- collect fresh verification evidence
- summarize what changed and why
- produce commit-level or PR-level review packs

## Rules

- no review-ready claim without verification evidence
- use `.harness/templates/evidence-pack.md` for raw evidence summaries
- use `.harness/templates/commit-pack.md` and `.harness/templates/pr-pack.md` for human review narratives
- promote durable PR narratives to `docs/reviews/` only when the change merits long-term retention

## Output

Produce a concise review pack that highlights scope, risks, verification evidence, doc updates, and deferred questions.
