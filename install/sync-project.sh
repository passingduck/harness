#!/usr/bin/env bash
set -euo pipefail
python3 -m harness_kit.cli sync-project "$@"
