# Phase 1 QA Rules

## Hook Points

- `rules/lint`: run the repository's configured static checks.
- `adversarial regression`: run focused regression probes for the changed surface area.
- `review stage`: attach evidence references to the matching review result.

## Command Placeholders

- Rules/lint command: `scripts/harness/run-qa.sh --stage rules-lint`
- Adversarial regression command: `scripts/harness/run-qa.sh --stage adversarial-regression`

Replace these placeholders with repo-specific commands when the project adopts concrete QA tooling.

## Required Evidence

- command invoked
- exit code
- key output
- files or interfaces checked
- follow-up action if the result is not `APPROVED`
