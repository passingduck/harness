#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHONPATH="$ROOT/scripts/harness/runtime${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m harness_kit.cli write-review-result --repo-root "$ROOT" "$@"
