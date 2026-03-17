# Repository Summary

## Module Map

- `harness_kit/cli.py`: distribution and generated-repo command entrypoint
- `harness_kit/scaffold.py`: project initialization, template copy/render, runtime vendoring, empty directory creation
- `harness_kit/template_loader.py`: template and skill file discovery plus placeholder rendering
- `harness_kit/runtime_bundle.py`: declares which modules are vendored into generated repos
- `harness_kit/queue.py`: queue-item validation, state transitions, and context-pack generation
- `harness_kit/worktree.py`: worktree path selection, registry records, open/close lifecycle
- `harness_kit/memory.py`: `DIRECTORY.md` refresh targeting and template-backed guide creation
- `harness_kit/review_pack.py`: review-pack draft creation and promotion into `docs/reviews/`

## Template Tree Summary

- `templates/project/AGENTS.md`: root operating contract for generated repos
- `templates/project/README.md`, `SUMMARY.md`, `REQUIREMENT.md`, `DIRECTORY.md`: baseline project docs
- `templates/project/.harness/policies/`: model routing, review stages, QA rules, and doc update policy
- `templates/project/.harness/templates/`: task, directory, context-pack, evidence-pack, commit-pack, and PR-pack markdown templates
- `templates/project/scripts/harness/`: generated shell wrappers for the vendored runtime commands and QA placeholder

## Vendored Runtime Map

Generated repositories receive these modules under `scripts/harness/runtime/harness_kit/`:

- `__init__.py`
- `cli.py`
- `memory.py`
- `queue.py`
- `review_pack.py`
- `worktree.py`

The scaffold intentionally does not vendor `scaffold.py` into generated repos, because `init` is a distribution-repo concern rather than a generated-repo runtime command.

## CLI Command Map

- `init --target --project-name`: create a new harness-enabled repository from the distribution repo
- `claim-task --repo-root --task`: move a ready queue item to `in_progress` and emit its context pack
- `open-worktree --repo-root --task-id --branch --cleanup-policy`: provision a task-local worktree and write the registry record
- `close-worktree --repo-root --task-id --mode --worker-status`: update the registry record and move the queue item to its next state
- `refresh-memory --repo-root --changed-path ...`: create or reuse impacted `DIRECTORY.md` guides
- `build-review-pack --repo-root --type --title --changed-path ... --verification-command ... [--promote-to ...]`: write a runtime review draft and optionally promote it into `docs/reviews/`
