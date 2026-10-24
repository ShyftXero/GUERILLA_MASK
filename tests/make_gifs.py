"""
Records short GIFs of each demo (and one of the full UI) by driving headless Chrome and
stitching stage screenshots with ffmpeg. Output: demos/<slug>.gif, demos/ui.gif.

Run:  cd tests && uv run --with playwright python -u -I make_gifs.py
Needs ffmpeg on PATH. Slow under software GL (~1 min per demo).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_guerilla_mask as T  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
FRAMES = 36          # frames per clip
FRAME_MS = 120       # capture interval (wall clock, headless is slow anyway)
GIF_FPS = 10
WIDTH = 640          # output gif width

SCENE_CYCLE = {       # which scenes to show, and how many frames each
    "kitchen-sink": [0, 1, 2, 3, 4],
    "wall-mandala": [0, 1, 2],
    "window-dodge": [0, 1, 2],
    "mirror-tunnel": [0, 1, 2],
}


def stitch(frames_dir, out, width):
    pal = Path(frames_dir) / "pal.png"
    base = ["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(GIF_FPS), "-i", str(Path(frames_dir) / "f%03d.png")]
    subprocess.run(base + ["-vf", f"scale={width}:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff", str(pal)], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(GIF_FPS), "-i", str(Path(frames_dir) / "f%03d.png"), "-i", str(pal),
                    "-lavfi", f"scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4", "-loop", "0", str(out)], check=True)


def record(page, locator, out, width, per_scene, scene_ids):
    with tempfile.TemporaryDirectory() as d:
        n = 0
        for sid in scene_ids:
            page.evaluate("(id) => recallScene(id)", sid)
            page.wait_for_timeout(600)
            for _ in range(per_scene):
                locator.screenshot(path=f"{d}/f{n:03d}.png")
                n += 1
                page.wait_for_timeout(FRAME_MS)
        stitch(d, out, width)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB, {n} frames)")


def main():
    httpd = T.serve()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=T.CHROME, args=[
            "--no-sandbox", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        page = browser.new_context(viewport={"width": 1280, "height": 720}).new_page()
        page.set_default_timeout(120000)
        page.goto(f"http://127.0.0.1:{T.PORT}/index.html")
        page.wait_for_timeout(800)
        page.evaluate("() => { confirmAction = async () => true; const d = document.getElementById('autosaveDiscardBtn'); if (d) d.click(); }")

        only = sys.argv[1:]
        for slug, scenes in SCENE_CYCLE.items():
            if only and slug not in only: continue
            text = (DEMOS / f"{slug}.json").read_text()
            page.evaluate("""async (t) => {
                app.mediaLibrary.forEach(stopMediaResources);
                await restoreFromSnapshot(JSON.parse(t), 'x');
                await new Promise(r => setTimeout(r, 2000));
                if (app.handlesVisible) toggleHandles();
                document.getElementById('stageTools').style.display = 'none';
                document.getElementById('hud').style.display = 'none';
            }""", text)
            ids = page.evaluate("() => app.scenes.map(s => s.id)")
            record(page, page.locator("#canvasContainer"), DEMOS / f"{slug}.gif", WIDTH, FRAMES // len(scenes), [ids[i] for i in scenes])

        if only: browser.close(); httpd.shutdown(); return
        # UI overview: window-dodge with handles, object selected, inspector open
        text = (DEMOS / "window-dodge.json").read_text()
        page.evaluate("""async (t) => {
            app.mediaLibrary.forEach(stopMediaResources);
            await restoreFromSnapshot(JSON.parse(t), 'x');
            await new Promise(r => setTimeout(r, 1500));
            if (!app.handlesVisible) toggleHandles();
            document.getElementById('stageTools').style.display = '';
            document.getElementById('hud').style.display = '';
            const P = app.layers.find(l => l.type === 'physics');
            selectObject(P.id, P.physics.objects[8].id);
        }""", text)
        ids = page.evaluate("() => app.scenes.map(s => s.id)")
        with tempfile.TemporaryDirectory() as d:
            n = 0
            for sid in ids[:2]:
                page.evaluate("(id) => { recallScene(id); const P = app.layers.find(l => l.type === 'physics'); selectObject(P.id, P.physics.objects[8].id); }", sid)
                page.wait_for_timeout(500)
                for _ in range(14):
                    page.screenshot(path=f"{d}/f{n:03d}.png")
                    n += 1
                    page.wait_for_timeout(FRAME_MS)
            stitch(d, DEMOS / "ui.gif", 960)
        print(f"wrote ui.gif ({(DEMOS / 'ui.gif').stat().st_size // 1024} KB)")
        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
