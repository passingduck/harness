# Project Name

Short description of the repository, its users, and its primary workflows.

## Getting Started

- install required tools
- review `AGENTS.md`
- read `SUMMARY.md` and `REQUIREMENT.md`
- inspect `third_party/harness-source.txt` to see which harness source commit last synced this repo

## Key Commands

- add setup commands
- add test commands
- add release or deploy commands
- `scripts/harness/write-review-result.sh` for required review-result receipts
- `scripts/harness/finish-worktree.sh` for the local review -> done landing step
- `scripts/harness/publish-pr.sh` for optional GitHub PR publication while the task is still in `review`

## Repository Map

- describe the main directories
- link to `DIRECTORY.md` files for local detail
- treat vendored runtime files under `scripts/harness/runtime/` as generated sync output rather than hand-edited source of truth
