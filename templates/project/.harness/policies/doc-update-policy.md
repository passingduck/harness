# Documentation Update Policy

Update durable docs whenever code, interfaces, or operational knowledge change.

## Required Checks

- `README.md` reflects user-facing setup or workflow changes.
- `SUMMARY.md` reflects architecture or operational changes.
- `REQUIREMENT.md` reflects environment or constraint changes.
- touched directories refresh `DIRECTORY.md` when local knowledge changed.
- `docs/specs/`, `docs/plans/`, and `docs/reviews/` stay consistent with the approved workflow.
- `.harness/policies/*`, `.harness/templates/*`, `skills/*`, and `scripts/harness/*` stay aligned when their contracts change.

If no durable docs changed, say why in the task report.
