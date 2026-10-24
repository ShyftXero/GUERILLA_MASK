#!/usr/bin/env bash
# Headless browser test for GUERILLA_MASK. Needs uv (https://docs.astral.sh/uv/) and a Chrome binary.
#   ./tests/run.sh
#   CHROME=/usr/bin/chromium ./tests/run.sh
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --with playwright python -u -I test_guerilla_mask.py "$@"
