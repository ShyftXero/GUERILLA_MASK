#!/usr/bin/env sh
# Serve GUERILLA_MASK over http://localhost:8000/ (needed for YouTube embeds; webcam/mic/MIDI work on localhost too).
cd "$(dirname "$0")"
PORT="${1:-8000}"
echo "GUERILLA_MASK -> http://localhost:$PORT/   (Ctrl+C to stop)"
if command -v python3 >/dev/null 2>&1; then exec python3 -m http.server "$PORT" --bind 127.0.0.1
elif command -v python >/dev/null 2>&1; then exec python -m SimpleHTTPServer "$PORT"
elif command -v npx >/dev/null 2>&1; then exec npx --yes serve -l "$PORT" .
else echo "Need python3, python, or npx on PATH"; exit 1; fi
