#!/usr/bin/env python3
"""
Compile GUERILLA_MASK into a single, truly-offline HTML file.

index.html keeps the gifler dependency as a CDN <script src> (convenient for dev).
This inlines the vendored copy so the built file needs no network at all.

The inlined library goes in its OWN <script> block appended right before </body> —
NOT spliced into the big inline app script — so it never lands in the middle of a
script block. gifler is only referenced at runtime (GIF playback), long after the
appended block has parsed, so load order is fine.

Usage:  python3 tools/build_offline.py        (writes dist/index.html)
Run with -I (isolated) since it reads vendored, third-party text.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
VENDOR = ROOT / "vendor" / "gifler.min.js"
OUT = ROOT / "dist" / "index.html"

# Matches the gifler CDN tag regardless of exact version/URL, on its own.
CDN_TAG = re.compile(r'[ \t]*<script\b[^>]*\bsrc=["\'][^"\']*gifler[^"\']*["\'][^>]*>\s*</script>\s*\n?',
                     re.IGNORECASE)


def die(msg):
    print(f"build_offline: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if not SRC.exists():
        die(f"{SRC} not found")
    if not VENDOR.exists():
        die(f"{VENDOR} not found — fetch it once:\n"
            f"  curl -fsSL https://unpkg.com/gifler@0.1.0/gifler.min.js -o {VENDOR.relative_to(ROOT)}")

    html = SRC.read_text(encoding="utf-8")
    vendor_js = VENDOR.read_text(encoding="utf-8")

    # 1. Remove the CDN <script src=...gifler...> tag (must find exactly one).
    tags = CDN_TAG.findall(html)
    if len(tags) != 1:
        die(f"expected exactly 1 gifler CDN <script src> tag, found {len(tags)} — "
            f"the source changed; update build_offline.py")
    html = CDN_TAG.sub("", html, count=1)

    # 2. Guard against the vendored JS prematurely closing the host <script>.
    safe_js = vendor_js.replace("</script>", "<\\/script>")

    block = (
        "    <!-- Vendored offline (was: unpkg gifler CDN). Inlined by tools/build_offline.py. -->\n"
        "    <script>\n" + safe_js.rstrip("\n") + "\n    </script>\n"
    )

    # 3. Append the vendor block in its own <script>, just before </body>.
    idx = html.rfind("</body>")
    if idx == -1:
        die("no </body> in index.html")
    html = html[:idx] + block + html[idx:]

    # 4. Sanity: no external script sources should remain in the built file.
    leftover = re.findall(r'<script\b[^>]*\bsrc=["\'](https?:)?//[^"\']+["\']', html, re.IGNORECASE)
    if leftover:
        die(f"external <script src> still present after build: {leftover}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024
    print(f"build_offline: wrote {OUT.relative_to(ROOT)} ({kb:.0f} KB) — gifler inlined, no network needed")


if __name__ == "__main__":
    main()
