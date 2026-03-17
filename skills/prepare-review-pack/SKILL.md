---
name: prepare-review-pack
description: Assemble phase-1 evidence and human-readable review packs from completed task work.
---

# Prepare Review Pack

Use this skill when code and documentation changes are ready for review.

## Goals

- collect fresh verification evidence
- turn evidence into a narrative-first explanation of what changed and why
- produce commit-level or PR-level review packs

## Rules

- no review-ready claim without verification evidence
- gather commands, exit codes, and key outputs first, then summarize them
- use `.harness/templates/evidence-pack.md` for raw evidence summaries while the task is in progress
- use `.harness/templates/commit-pack.md` and `.harness/templates/pr-pack.md` for human review narratives
- use `scripts/harness/build-review-pack.sh` to create runtime drafts under `.harness/runtime/review-packs/drafts/`
- keep durable raw evidence out of `docs/reviews/`; promoted docs should be narrative summaries with the necessary verification evidence, not a dump of terminal output
- promote durable PR narratives to `docs/reviews/` only when the change merits long-term retention

## Workflow

1. Run the required verification commands and capture the evidence you need.
2. Distill that evidence into the claim being justified:
   - what changed
   - why it changed
   - intended scope
   - major risks
   - documentation updates
   - deferred questions
3. Generate a runtime draft with `scripts/harness/build-review-pack.sh`.
4. Edit the draft so the top-level story is human-readable before anyone has to inspect raw command output.
5. If the work needs a durable narrative, promote the draft into `docs/reviews/` and keep only the narrative plus concise verification evidence there.

## Output

Produce a concise review pack that highlights scope, risks, verification evidence, doc updates, and deferred questions, with the narrative leading and the evidence supporting it.
