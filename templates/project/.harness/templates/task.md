---
id: task-0001
title: Short task title
status: ready
priority: medium
owner_role: implementer
model_hint: gpt-5.4
worktree: null
parent_spec: docs/specs/example-spec.md
parent_plan: docs/plans/example-plan.md
why_this_task_exists: Explain the decision or gap this task resolves.
owned_paths:
  - path/to/owned/file
required_reads:
  - AGENTS.md
disallowed_edits:
  - path/to/protected/file
docs_to_update:
  - SUMMARY.md
constraints:
  - Preserve existing public behavior unless the task says otherwise.
verification_commands:
  - pytest path/to/tests
expected_report_schema:
  - Status
  - What you implemented
  - What you tested and results
  - Files changed
  - Commit SHA
  - Self-review findings
  - Any issues or concerns
review_stages:
  - rules_lint_review
  - adversarial_regression_review
dependencies: []
---

The directory name is authoritative for queue state. Frontmatter `status` must mirror the parent directory name.

## task_text

Describe the requested change, scope boundaries, and any context the implementer must preserve.

## acceptance_criteria

- describe observable outcomes
- include required documentation updates
- include required verification

## non_goals

- call out work that is explicitly out of scope
