# Repository Summary

## Purpose

State the problem this repository solves and the boundaries it owns.

## Architecture Snapshot

Summarize major components, data flows, and operational assumptions.

## Key Workflows

- implementation flow
- review flow
- release or deploy flow
- `write-review-result` records stage receipts under `.harness/runtime/review-results/`
- `finish-worktree` lands a review-state task locally and finalizes queue and registry state
- `publish-pr` is optional and only for GitHub publication while the task remains in `review`
- `third_party/harness-source.txt` records the last harness scaffold or sync provenance

## Known Risks

Capture the highest-signal risks, constraints, and operational caveats.
