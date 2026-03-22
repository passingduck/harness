#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$ROOT/scripts/harness/runtime${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m harness_kit.cli claim-task --repo-root "$ROOT" "$@"
