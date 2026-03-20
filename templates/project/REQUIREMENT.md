# Requirements

## Environment

- language and runtime versions
- package manager and system dependencies
- `gh` is optional and only required when using `publish-pr`

## Constraints

- external service assumptions
- security, compliance, or reliability constraints
- compatibility guarantees
- vendored runtime files under `scripts/harness/runtime/` are generated and refreshed by the distribution repo
- `third_party/harness-source.txt` is the durable provenance record for the last scaffold or sync

## Non-Negotiables

- document the rules that must remain true during implementation and operations
