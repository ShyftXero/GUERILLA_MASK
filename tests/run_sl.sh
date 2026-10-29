#!/usr/bin/env bash
# Headless browser test for the GUERILLA_MASK structured-light core. Needs uv and a Chrome binary.
#   ./tests/run_sl.sh
#   CHROME=/usr/bin/chromium ./tests/run_sl.sh
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --with playwright python -u -I test_structured_light.py "$@"
