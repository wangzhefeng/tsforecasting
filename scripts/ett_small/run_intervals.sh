#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

exec uv run python -m tsforecasting.main_cli \
  "run" \
  --config "configs/examples/ett_small/intervals.yaml" \
  "$@"
