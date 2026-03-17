# Requirements

## Environment Assumptions

- Python: `python3` must be available, and phase 1 assumes a modern Python 3 interpreter that can run the standard-library-only `harness_kit` package and `python3 -m unittest`.
- Git: `git` must be available for repositories that use the phase-1 worktree flow. Non-git temp directories are supported for basic local scaffolding tests, but real worktree orchestration assumes a normal git worktree-capable repository.
- Shell: generated wrapper scripts assume a POSIX shell environment with `bash`.

## Deterministic Adapter Rule

Phase 1 keeps the canonical source of truth in the repo-native markdown, policy, and runtime files. Any adapter or wrapper generated from those files must be deterministic:

- identical source inputs must produce identical generated outputs
- generated adapters may not introduce behavior that is absent from the canonical files
- generated adapters must not become the authoritative source of truth

This is why the generated repos vendor a fixed subset of `harness_kit` runtime modules instead of depending on mutable external tooling.

## Codex-First Support Statement

Phase 1 is explicitly Codex-first. The distribution repo ships:

- Codex-oriented scaffold defaults in `templates/project/AGENTS.md`
- Codex workflow skills in `skills/`
- a Codex adapter note in `adapters/codex/README.md`

Support for Claude Code and GitHub Copilot CLI is intentionally excluded from phase 1 implementation. Their future adapters must derive from the same canonical contracts instead of redefining them.

## Additional Constraints

- Standard library only for the Python implementation
- Documentation is written in English
- Commit messages are written in Korean
- Queue state is directory-authoritative in generated repos
