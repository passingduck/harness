# harness-kit

`harness-kit` builds a repo-native, Codex-first phase-1 harness for task orchestration, worktree lifecycle tracking, directory memory refresh, and review-pack generation. The distribution repo owns the Python runtime, scaffold templates, installer entrypoint, and the tests that prove the generated repo works end to end.

## Phase 1 Includes

- `python3 -m harness_kit.cli init` to scaffold a new harness-enabled repository
- canonical project templates under `templates/project/`
- vendored runtime modules copied into generated repos under `scripts/harness/runtime/harness_kit/`
- phase-1 commands for `claim-task`, `open-worktree`, `close-worktree`, `refresh-memory`, and `build-review-pack`
- queue, worktree, memory, and review-pack tests in `tests/`

## Phase 1 Excludes

- phase-2 controller features, daemons, or dashboards
- packaged Claude or Copilot adapters
- `adopt-project.sh` and `upgrade-project.sh`
- language-specific lint/test adapter packs beyond the phase-1 shell placeholders

## Initialize A Project

Run the installer wrapper from the distribution repo root:

```bash
./install/init-project.sh --target /path/to/project --project-name demo
```

This shells into `python3 -m harness_kit.cli init`, renders the project templates, vendors the runtime bundle, and creates the empty runtime directories a fresh repo needs.

## Run Tests

Run the full Python suite:

```bash
python3 -m unittest discover -s tests -v
```

Run the scaffold-focused tests only:

```bash
python3 -m unittest tests.test_scaffold -v
```

## Phase 1 Layout

- `harness_kit/`: standard-library implementation for scaffold generation and generated-repo runtime commands
- `templates/project/`: canonical files copied into generated repositories
- `skills/`: Codex-oriented workflow skills copied into generated repositories
- `install/`: thin shell wrappers for distribution-repo entrypoints
- `tests/`: phase-1 verification for scaffold, queue, worktree, memory, and review-pack flows
