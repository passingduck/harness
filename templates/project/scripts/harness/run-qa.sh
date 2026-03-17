#!/usr/bin/env bash
set -euo pipefail

stage="all"
if [[ "${1:-}" == "--stage" ]]; then
  stage="${2:-}"
fi

case "$stage" in
  all|rules-lint|adversarial-regression)
    printf 'Phase 1 QA placeholder for stage: %s\n' "$stage"
    printf 'Configure concrete commands in .harness/policies/qa-rules.md\n'
    ;;
  *)
    printf 'Usage: %s [--stage all|rules-lint|adversarial-regression]\n' "$0" >&2
    exit 2
    ;;
esac
