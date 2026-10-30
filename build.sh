#!/usr/bin/env sh
# Compile GUERILLA_MASK into a single truly-offline file at index.offline.html
# (inlines the vendored gifler library; no CDN, no network).
#   ./build.sh
cd "$(dirname "$0")"
exec python3 -I tools/build_offline.py "$@"
