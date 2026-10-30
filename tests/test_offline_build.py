"""
Verify the compiled single file (dist/index.html) is truly offline-capable.

Builds it, then loads it with ALL non-local network blocked and asserts gifler is
defined (inlined, not fetched) and the app initialised with no page errors.

Run:  uv run --with playwright python -u -I tests/test_offline_build.py
"""
import os
import sys
import subprocess
import threading
import http.server
import socketserver
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("GM_OFFLINE_PORT", "8781"))
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
FAILS = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        FAILS.append(name)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "build_offline.py")], check=True)
    built = ROOT / "index.offline.html"
    check("index.offline.html built", built.exists())

    os.chdir(ROOT)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    errors, blocked = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=[
            "--no-sandbox", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        page = browser.new_context(viewport={"width": 1200, "height": 800}).new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))

        # Block every request that isn't our local server — simulates true offline.
        def route(r):
            url = r.request.url
            if url.startswith(f"http://127.0.0.1:{PORT}") or url.startswith("data:") or url.startswith("blob:"):
                r.continue_()
            else:
                blocked.append(url)
                r.abort()
        page.context.route("**/*", route)

        page.goto(f"http://127.0.0.1:{PORT}/index.offline.html")
        page.wait_for_timeout(1000)

        state = page.evaluate("""() => ({
            gifler: typeof gifler !== 'undefined',
            app: typeof app !== 'undefined' && Array.isArray(app.layers),
            sl: typeof app !== 'undefined' && !!app.sl,
            mapBtn: !!document.getElementById('slMapBtn')
        })""")
        check("gifler inlined (defined with network blocked)", state["gifler"])
        check("app initialised offline", state["app"] and state["sl"])
        check("structured-light UI present", state["mapBtn"])
        check("no external requests needed (none blocked)", not blocked, str(blocked[:3]))
        check("no page errors", not errors, str(errors[:3]))
        browser.close()
    httpd.shutdown()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILED: {FAILS}")
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
