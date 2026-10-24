"""
Builds the demo projects in demos/ by driving the real app in headless Chrome, so the
JSON is exactly what Save produces. Also captures a screenshot of each demo.

Run:  cd tests && uv run --with playwright python -u -I make_demos.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_guerilla_mask as T  # noqa: E402  (reuses serve/CHROME/PORT)
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
DEMOS.mkdir(exist_ok=True)

RESET = """
async () => {
  confirmAction = async () => true; const d = document.getElementById('autosaveDiscardBtn');
  if (d && document.getElementById('autosaveModal').classList.contains('visible')) d.click();
  app.mediaLibrary.forEach(stopMediaResources);
  app.mediaLibrary = []; app.layers = []; app.scenes = []; app.activeSceneId = null; midi.ccMaps = [];
  app.selectedLayerId = null; app.addingPoints = false; app.pcToScene = false;
  updateMediaList(); updateLayerList(); updateOverlay(); updateSceneList();
}
"""

HELPERS = """
window.demo = {
  gen(key, params = {}, name = null, extra = {}) {
    const m = createGeneratorMedia(key, params, null, name);
    Object.assign(m, extra);
    upsertMedia(m); tickGenerator(m, 0); return m;
  },
  quad(name, media, pts) {
    const L = { id: uuid(), type: 'projection', name, mediaId: media ? media.id : null, mediaName: media ? media.name : null, enabled: true, points: pts.map(([x,y]) => ({x,y})) };
    app.layers.push(L); return L;
  },
  mask(name, pts) {
    const L = { id: uuid(), type: 'mask', name, mediaId: null, mediaName: null, enabled: true, points: pts.map(([x,y]) => ({x,y})) };
    app.layers.push(L); return L;
  },
  physics(name, pts, settings = {}) {
    const L = { id: uuid(), type: 'physics', name, mediaId: null, mediaName: null, enabled: true, points: pts.map(([x,y]) => ({x,y})), physics: { ...PHYSICS_DEFAULTS(), ...settings } };
    app.layers.push(L); app.selectedLayerId = L.id; return L;
  },
  scene(name) { const s = captureScene(name); app.scenes.push(s); app.activeSceneId = s.id; return s; },
  rect(cx, cy, w, h) { return [[cx-w/2, cy-h/2],[cx+w/2, cy-h/2],[cx+w/2, cy+h/2],[cx-w/2, cy+h/2]]; },
  finish() { updateMediaList(); updateLayerList(); updateOverlay(); updateSceneList(); }
};
"""

DEMO_MANDALA = """
async () => {
  const D = window.demo;
  const plasma = D.gen('plasma', { speed: 0.8, scale: 1.4, hue: 280 }, 'Plasma core');
  const kal = D.gen('kaleido', { sym: 8, scale: 1, hue: 300, rot: 0.01, zoom: 1.0 }, 'Mandala', { sourceId: plasma.id, sourceName: plasma.name, mods: [{ signal: 'bass', param: 'sym', amount: 0.5 }] });
  const hex = D.gen('hexagons', { speed: 1.2, scale: 1.6, hue: 190 }, 'Hex wing', { mods: [{ signal: 'mid', param: 'speed', amount: 0.6 }] });
  const lasers = D.gen('lasers', { speed: 1, scale: 1.2, hue: 20 }, 'Laser wing', { mods: [{ signal: 'high', param: 'scale', amount: 0.5 }], beatHue: true });
  const circles = D.gen('circles', { speed: 0.9, scale: 1.1, hue: 120 }, 'Ripples');
  const rd = D.gen('reaction', { feed: 0.037, kill: 0.06, hue: 330, speed: 1 }, 'Coral');

  // Look 1: wall triptych
  D.quad('Left wing', hex, [[3,20],[30,15],[30,85],[3,80]]);
  D.quad('Center', kal, D.rect(50, 50, 38, 70));
  D.quad('Right wing', lasers, [[70,15],[97,20],[97,80],[70,85]]);
  D.mask('Doorway', D.rect(50, 78, 12, 44));   // keep the door clear
  D.scene('Triptych');

  // Look 2: ripples + coral, same geometry
  app.layers[0].mediaId = circles.id; app.layers[0].mediaName = circles.name;
  app.layers[1].mediaId = rd.id; app.layers[1].mediaName = rd.name;
  app.layers[2].mediaId = circles.id; app.layers[2].mediaName = circles.name;
  D.scene('Coral');

  // Look 3: single wide mandala
  app.layers[0].enabled = false; app.layers[2].enabled = false;
  app.layers[1].mediaId = kal.id; app.layers[1].mediaName = kal.name;
  app.layers[1].points = D.rect(50, 50, 94, 90).map(([x,y]) => ({x,y}));
  D.scene('Full mandala');

  recallScene(app.scenes[0].id);
  D.finish();
  return app.layers.length;
}
"""

DEMO_DODGE = """
async () => {
  const D = window.demo;
  const rd = D.gen('reaction', { feed: 0.055, kill: 0.062, hue: 40, speed: 1.2 }, 'Spore');
  const plasma = D.gen('plasma', { speed: 1.5, scale: 2, hue: 200 }, 'Plasma ball');
  const stripes = D.gen('stripes', { speed: 1, scale: 1.2, hue: 0 }, 'Warning stripes');

  // Two windows and a sign to dodge
  D.mask('Window left', D.rect(25, 35, 22, 30));
  D.mask('Window right', D.rect(75, 35, 22, 30));
  D.mask('Sign', [[40,70],[60,70],[62,82],[38,82]]);

  const P = D.physics('Dodge arena', [], { gravity: 0.35, speed: 1, bounce: 0.9, size: 5, spin: 1.5, trail: 0.6, beatKick: true, mod: { signal: 'bass', param: 'size', amount: 0.4 } });
  const shapes = ['circle','hexagon','triangle','rect','circle','hexagon','circle','triangle'];
  shapes.forEach(s => P.physics.objects.push(makePhysicsObject(P, { kind: 'shape', shape: s })));
  P.physics.objects.push(makePhysicsObject(P, { kind: 'media', mediaId: rd.id, mediaName: rd.name, r: 10, rotV: 0.3 }));
  P.physics.objects.push(makePhysicsObject(P, { kind: 'media', mediaId: plasma.id, mediaName: plasma.name, r: 8, rotV: -0.5 }));
  D.scene('Bounce');

  // Look 2: zero-g pinball, no trails, stripes behind
  const bg = D.quad('Backdrop', stripes, D.rect(50, 50, 100, 100));
  app.layers.unshift(app.layers.pop()); // backdrop to the bottom
  P.physics.gravity = 0; P.physics.trail = 0; P.physics.speed = 1.6; P.physics.bounce = 1.05;
  D.scene('Zero-G pinball');

  // Look 3: heavy rain
  bg.enabled = false;
  P.physics.gravity = 1.2; P.physics.trail = 0.85; P.physics.bounce = 0.6; P.physics.speed = 1;
  D.scene('Heavy rain');

  recallScene(app.scenes[0].id);
  D.finish();
  return app.layers.length;
}
"""

DEMO_MIRROR = """
async () => {
  const D = window.demo;
  // Webcam stub: the real stream is requested on load (needs a click if the browser asks).
  const cam = { id: uuid(), name: 'Webcam', type: 'camera', kind: 'camera', element: null, width: 0, height: 0, filename: 'Webcam', needsRelink: true };
  app.mediaLibrary.push(cam);
  // Motion Cut strips the static background: only people moving in front of the camera reach the wall.
  const cut = D.gen('motioncut', { learn: 0.02, threshold: 0.16, soft: 0.08, hold: 0.95, ghost: 0, tint: 0 }, 'Motion cut',
      { sourceId: cam.id, sourceName: 'Webcam' });
  const skin = D.gen('reaction', { feed: 0.03, kill: 0.057, seed: 0.9, hue: 120, speed: 1.2 }, 'Alien skin',
      { sourceId: cut.id, sourceName: cut.name, mods: [{ signal: 'motion', param: 'feed', amount: 0.3 }] });
  const tunnel = D.gen('feedback', { decay: 0.955, zoom: 1.015, warp: 0.006, rot: 0.006, sym: 6, hueShift: 0.05, edge: 0.35, hue: 200 }, 'Mirror tunnel',
      { sourceId: cut.id, sourceName: cut.name, mods: [{ signal: 'motion', param: 'zoom', amount: 0.5 }], beatHue: true });
  const ghost = D.gen('motioncut', { learn: 0.01, threshold: 0.14, soft: 0.1, hold: 0.985, ghost: 0.08, tint: 0.7, hue: 300 }, 'Neon ghost',
      { sourceId: cam.id, sourceName: 'Webcam', mods: [{ signal: 'beat', param: 'hue', amount: 0.5 }] });
  const kal = D.gen('kaleido', { sym: 12, hue: 0, rot: 0.003, edge: 0 }, 'Face mandala', { sourceId: cut.id, sourceName: cut.name });

  D.quad('Wall', skin, D.rect(50, 50, 96, 92));
  D.scene('Alien skin');

  app.layers[0].mediaId = tunnel.id; app.layers[0].mediaName = tunnel.name;
  D.scene('Tunnel');

  app.layers[0].mediaId = ghost.id; app.layers[0].mediaName = ghost.name;
  D.scene('Neon ghost');

  app.layers[0].mediaId = kal.id; app.layers[0].mediaName = kal.name;
  D.scene('Mandala');

  // Split: skin left, tunnel right
  app.layers[0].mediaId = skin.id; app.layers[0].mediaName = skin.name;
  app.layers[0].points = D.rect(26, 50, 48, 92).map(([x,y]) => ({x,y}));
  D.quad('Wall right', tunnel, D.rect(74, 50, 48, 92));
  D.scene('Split');

  recallScene(app.scenes[0].id);
  D.finish();
  return app.layers.length;
}
"""

DEMO_KITCHEN = """
async () => {
  const D = window.demo;
  // --- every media kind ---
  const cam = { id: uuid(), name: 'Webcam', type: 'camera', kind: 'camera', element: null, width: 0, height: 0, filename: 'Webcam', needsRelink: true };
  app.mediaLibrary.push(cam);
  const yt = createYouTubeMedia('jNQXAC9IVRw', null, 'YouTube: Me at the zoo'); upsertMedia(yt);
  const mp4 = createRemoteVideoMedia('https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4', null, 'Remote mp4 (flower)'); upsertMedia(mp4);
  const plasma = D.gen('plasma', { speed: 0.9, scale: 1.3, hue: 200 }, 'Plasma', { mods: [{ signal: 'bass', param: 'scale', amount: 0.5 }], beatHue: true });
  const perlin = D.gen('perlin', { speed: 0.6, scale: 1, hue: 30 }, 'Perlin');
  const lasers = D.gen('lasers', { speed: 1.2, scale: 1, hue: 0 }, 'Lasers', { mods: [{ signal: 'high', param: 'scale', amount: 0.6 }] });
  const hex = D.gen('hexagons', { speed: 1, scale: 1.5, hue: 160 }, 'Hexagons', { mods: [{ signal: 'mid', param: 'speed', amount: 0.5 }] });
  const tri = D.gen('triangles', { speed: 1, scale: 1.2, hue: 300 }, 'Triangles');
  const circ = D.gen('circles', { speed: 0.8, scale: 1, hue: 90 }, 'Circles');
  const rects = D.gen('rectangles', { speed: 1, scale: 1, hue: 45 }, 'Rectangles');
  const stripes = D.gen('stripes', { speed: 0.7, scale: 1, hue: 0 }, 'Stripes');
  const cut = D.gen('motioncut', { learn: 0.02, threshold: 0.16, soft: 0.08, hold: 0.95, ghost: 0, tint: 0.4, hue: 280 }, 'Motion cut', { sourceId: cam.id, sourceName: 'Webcam' });
  const skin = D.gen('reaction', { feed: 0.03, kill: 0.057, seed: 0.9, hue: 120, wiggle: 0.015, wfreq: 9, glow: 0.4 }, 'Alien skin', { sourceId: cut.id, sourceName: cut.name, mods: [{ signal: 'motion', param: 'feed', amount: 0.3 }] });
  const tunnel = D.gen('feedback', { decay: 0.95, zoom: 1.012, warp: 0.005, rot: 0.005, sym: 6, hueShift: 0.04, edge: 0.4, hue: 200 }, 'Tunnel', { sourceId: cut.id, sourceName: cut.name, mods: [{ signal: 'motion', param: 'zoom', amount: 0.5 }], beatHue: true });
  const kal = D.gen('kaleido', { sym: 8, hue: 0, rot: 0.01, edge: 0 }, 'Kaleido of plasma', { sourceId: plasma.id, sourceName: plasma.name, mods: [{ signal: 'bass', param: 'sym', amount: 0.5 }] });
  const neon = D.gen('filter', { mode: 1, amount: 0.6, hue: 200 }, 'Neon edges', { sourceId: cam.id, sourceName: 'Webcam' });
  const poster = D.gen('filter', { mode: 2, amount: 0.5, hue: 0 }, 'Posterize', { sourceId: cam.id, sourceName: 'Webcam' });
  const pixel = D.gen('filter', { mode: 4, amount: 0.5, scale: 1.5, hue: 0 }, 'Pixelate', { sourceId: mp4.id, sourceName: mp4.name });

  // --- Scene 1: the grid (one quad per media kind) ---
  const cell = (c, r) => D.rect(12.5 + c * 25, 17 + r * 33, 22, 28);
  D.quad('Plasma', plasma, cell(0, 0));
  D.quad('Perlin', perlin, cell(1, 0));
  D.quad('Lasers', lasers, cell(2, 0));
  D.quad('Hexagons', hex, cell(3, 0));
  D.quad('Triangles', tri, cell(0, 1));
  D.quad('Circles', circ, cell(1, 1));
  D.quad('Rectangles', rects, cell(2, 1));
  D.quad('Stripes', stripes, cell(3, 1));
  D.quad('Kaleido', kal, cell(0, 2));
  D.quad('YouTube', yt, cell(1, 2));
  D.quad('Remote mp4', mp4, cell(2, 2));
  D.quad('Webcam', cam, cell(3, 2));
  D.scene('Grid: every source');

  // --- Scene 2: effects on the webcam, full wall, doorway masked ---
  app.layers = [];
  D.quad('Skin', skin, D.rect(26, 50, 48, 92));
  D.quad('Tunnel', tunnel, D.rect(74, 50, 48, 92));
  D.mask('Doorway', D.rect(50, 80, 14, 40));
  D.scene('Webcam effects');

  // --- Scene: camera filters side by side ---
  app.layers = [];
  D.quad('Raw', cam, D.rect(12.5, 30, 23, 50));
  D.quad('Neon edges', neon, D.rect(37.5, 30, 23, 50));
  D.quad('Posterize', poster, D.rect(62.5, 30, 23, 50));
  D.quad('Pixelate mp4', pixel, D.rect(87.5, 30, 23, 50));
  D.quad('Motion cut', cut, D.rect(50, 78, 96, 36));
  D.scene('Camera filters');

  // --- Scene 3: physics over a warped YouTube backdrop ---
  app.layers = [];
  D.quad('Backdrop', yt, [[8,6],[92,12],[95,94],[5,88]]);
  D.mask('Window', D.rect(50, 40, 20, 24));
  const P = D.physics('Arena', [], { gravity: 0.3, speed: 1, bounce: 0.9, size: 5, spin: 1.5, trail: 0.5, beatKick: true, mod: { signal: 'bass', param: 'size', amount: 0.4 } });
  ['circle', 'hexagon', 'triangle', 'rect', 'circle'].forEach(s => P.physics.objects.push(makePhysicsObject(P, { kind: 'shape', shape: s })));
  P.physics.objects.push(makePhysicsObject(P, { kind: 'media', mediaId: skin.id, mediaName: skin.name, r: 9, rotV: 0.4 }));
  P.physics.objects.push(makePhysicsObject(P, { kind: 'media', mediaId: mp4.id, mediaName: mp4.name, r: 9, rotV: -0.3, alpha: 0.6 }));
  P.physics.objects.push(makePhysicsObject(P, { kind: 'shape', shape: 'circle', r: 12, alpha: 0.35, color: 'hsl(200, 90%, 55%)' }));
  P.physics.objects.push(makePhysicsObject(P, { kind: 'media', mediaId: plasma.id, mediaName: plasma.name, r: 7, rotV: 0.6, enabled: false })); // one hidden
  D.scene('Physics over YouTube');

  // --- Scene 4: mandala wall ---
  app.layers = [];
  D.quad('Left', hex, [[3,20],[30,15],[30,85],[3,80]]);
  D.quad('Center', kal, D.rect(50, 50, 38, 70));
  D.quad('Right', lasers, [[70,15],[97,20],[97,80],[70,85]]);
  D.scene('Mandala wall');

  // --- MIDI + settings sample bindings ---
  app.scenes.forEach((s, i) => { s.note = 36 + i; });
  midi.ccMaps = [
    { cc: 1, channel: 0, target: `gen:${plasma.name}:speed`, min: 0, max: 4 },
    { cc: 2, channel: 0, target: `gen:${tunnel.name}:zoom`, min: 0.95, max: 1.05 },
    { cc: 3, channel: 0, target: `gen:${skin.name}:wiggle`, min: 0, max: 0.06 },
    { cc: 7, channel: 0, target: 'phys:gravity', min: 0, max: 2 }
  ];
  app.pcToScene = true;
  app.bumpKey = ' ';

  recallScene(app.scenes[0].id);
  D.finish();
  return app.layers.length;
}
"""

DEMOS_SPEC = [
    ("kitchen-sink", "Kitchen Sink", DEMO_KITCHEN),
    ("wall-mandala", "Wall Mandala", DEMO_MANDALA),
    ("window-dodge", "Window Dodge", DEMO_DODGE),
    ("mirror-tunnel", "Mirror Tunnel", DEMO_MIRROR),
]


def main():
    httpd = T.serve()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=T.CHROME, args=[
            "--no-sandbox", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        page = browser.new_context(viewport={"width": 1280, "height": 720}).new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{T.PORT}/index.html")
        page.wait_for_timeout(800)
        page.evaluate(HELPERS)
        for slug, title, js in DEMOS_SPEC:
            page.evaluate(RESET)
            n = page.evaluate(js)
            page.wait_for_timeout(2500)
            snap = page.evaluate("async () => JSON.stringify(await buildProjectSnapshot(true))")
            data = json.loads(snap)
            data["title"] = title
            out = DEMOS / f"{slug}.json"
            out.write_text(json.dumps(data, indent=1))
            page.evaluate("() => { if (app.handlesVisible) toggleHandles(); }")
            page.wait_for_timeout(300)
            page.locator("#canvasContainer").screenshot(path=str(DEMOS / f"{slug}.png"))
            page.evaluate("() => { if (!app.handlesVisible) toggleHandles(); }")
            print(f"wrote {out.name}: {n} layers, {len(data['scenes'])} scenes, {out.stat().st_size // 1024} KB")
        # Round-trip each demo through Load to prove they open clean
        for slug, title, _ in DEMOS_SPEC:
            page.evaluate(RESET)
            text = (DEMOS / f"{slug}.json").read_text()
            r = page.evaluate("""async (text) => {
                await restoreFromSnapshot(JSON.parse(text), 'Project loaded');
                await new Promise(r => setTimeout(r, 3500));
                const missing = app.mediaLibrary.filter(m => m.needsRelink && m.kind !== 'camera').length;
                const unlinked = app.layers.filter(l => l.type === 'projection' && !l.mediaId).length;
                const gens = app.mediaLibrary.filter(m => m.kind === 'generator');
                const badSrc = gens.filter(g => g.sourceName && !g.sourceId).length;
                return { layers: app.layers.length, scenes: app.scenes.length, missing, unlinked, badSrc, midi: midi.ccMaps.length };
            }""", text)
            ok = r["missing"] == 0 and r["unlinked"] == 0 and r["badSrc"] == 0
            print(f"[{'PASS' if ok else 'FAIL'}] load {slug}: {json.dumps(r)}")
        print("errors:", errors)
        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
