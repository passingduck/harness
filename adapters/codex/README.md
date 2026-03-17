# Codex Adapter Notes

Generated repositories are self-contained for Codex-first work:

- `AGENTS.md` is copied into the repository root and defines the repo-local operating rules.
- `skills/` is copied into the repository root so Codex can resolve the canonical skill bodies locally.
- `scripts/harness/runtime/harness_kit/` contains the vendored repo-local runtime bundle used by generated repositories.

Some Codex environments may still need external skill discovery. In those cases, add an optional fallback helper that links the generated repo's `skills/` directory into the environment-specific discovery path instead of relying on shared global state.
