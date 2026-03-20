#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHONPATH="$ROOT/scripts/harness/runtime${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m harness_kit.cli finish-worktree --repo-root "$ROOT" "$@"
