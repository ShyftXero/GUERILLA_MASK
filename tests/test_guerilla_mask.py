"""
Headless browser tests for GUERILLA_MASK.

Run:  ./tests/run.sh          (needs uv; uses system Chrome at /usr/bin/google-chrome or $CHROME)

Covers: patterns render, physics respects masks/arena, scenes + MIDI, IndexedDB autosave,
self-contained Save/Load, GIF/video relink from cache, undo delete, blackout, name-collision guard.
"""
import json
import os
import sys
import time
import threading
import http.server
import socketserver
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("GM_TEST_PORT", "8777"))
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
SHOTS = Path(__file__).resolve().parent / "screenshots"
SHOTS.mkdir(exist_ok=True)

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not cond:
        FAILS.append(name)


def _png(w, h, rgb):
    """Minimal solid-colour PNG (stdlib only). Multipart image parts may be any image type Chrome decodes."""
    import struct, zlib
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


MJPEG_FRAMES = [_png(64, 48, (255, 0, 0)), _png(64, 48, (0, 0, 255))]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        # /test.mjpg[?cors=1][&frames=N]: an MJPEG-style multipart/x-mixed-replace stream, alternating red/blue.
        if self.path.startswith("/test.mjpg"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            frames = int(q.get("frames", ["40"])[0])
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            if q.get("cors"):
                self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                for i in range(frames):
                    f = MJPEG_FRAMES[i % 2]
                    self.wfile.write(b"--frame\r\nContent-Type: image/png\r\nContent-Length: %d\r\n\r\n" % len(f) + f + b"\r\n")
                    self.wfile.flush()
                    time.sleep(0.1)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        return super().do_GET()


def serve(port=PORT):
    os.chdir(ROOT)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


JS_SETUP = """
async () => {
  window._realConfirm = confirmAction; confirmAction = async () => true; // auto-accept destructive prompts in tests
  const d = document.getElementById('autosaveDiscardBtn');
  if (d && document.getElementById('autosaveModal').classList.contains('visible')) d.click();
  const out = {};
  await startWebcam(); await startMic();
  const cam = app.mediaLibrary.find(m => m.kind === 'camera');
  out.cam = !!(cam && cam.element && cam.element.videoWidth > 0);
  for (const k of ['plasma', 'hexagons', 'feedback', 'reaction']) addGeneratorByKey(k);
  // C4: delete Plasma 1, add plasma again -> must NOT collide with any existing name
  const names0 = app.mediaLibrary.map(m => m.name);
  addGeneratorByKey('plasma');
  const p2 = app.mediaLibrary.find(m => m.name === 'Plasma 2');
  app.mediaLibrary = app.mediaLibrary.filter(m => m.name !== 'Plasma 1');
  addGeneratorByKey('plasma');
  out.uniqueNames = new Set(app.mediaLibrary.map(m => m.name)).size === app.mediaLibrary.length;
  out.plasma2Survived = app.mediaLibrary.some(m => m.id === p2.id);
  // synthetic media: a PNG image, a tiny GIF, via blobs (exercise loader + cache)
  const c = document.createElement('canvas'); c.width = 64; c.height = 64; const x = c.getContext('2d');
  x.fillStyle = '#f0f'; x.fillRect(0, 0, 64, 64);
  const pngBlob = await new Promise(r => c.toBlob(r, 'image/png'));
  const png = new File([pngBlob], 'test-image.png', { type: 'image/png' });
  const gifBytes = Uint8Array.from(atob('R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='), ch => ch.charCodeAt(0));
  const gif = new File([gifBytes], 'test-anim.gif', { type: 'image/gif' });
  const img = await loadMediaFile(png);
  const g = await loadMediaFile(gif);
  out.imgLoaded = !!(img && img.element && img.width === 64);
  out.gifLoaded = !!(g && g.element);
  // layers
  app.layerType = 'projection'; createLayer();
  let L = app.layers[0]; L.points = [{x:5,y:5},{x:45,y:5},{x:45,y:45},{x:5,y:45}]; L.mediaId = img.id; L.mediaName = img.name;
  createLayer(); L = app.layers[1]; L.points = [{x:50,y:5},{x:95,y:5},{x:95,y:45},{x:50,y:45}];
  const fb = app.mediaLibrary.find(m => m.gen === 'feedback'); L.mediaId = fb.id; L.mediaName = fb.name;
  app.layerType = 'mask'; createLayer(); L = app.layers[2]; L.points = [{x:60,y:60},{x:80,y:60},{x:80,y:80},{x:60,y:80}];
  app.layerType = 'physics'; createLayer(); app.addingPoints = false;
  const P = app.layers[3]; P.points = [{x:50,y:50},{x:95,y:50},{x:95,y:95},{x:50,y:95}];
  addShapeObject('circle'); addShapeObject('hexagon'); useMediaInSelectedLayer(g); useMediaInSelectedLayer(cam);
  for (let i = 0; i < 60; i++) addShapeObject('rect');
  out.objectCap = P.physics.objects.length;
  P.physics.objects.length = 12; // realistic show count for the collision checks below
  app.addingPoints = false;
  addScene();
  app.layers[0].enabled = false; addScene();
  midi.learn = { type: 'scene', sceneId: app.scenes[0].id }; onMidiMessage({ data: [0x90, 40, 100] });
  midi.learn = { type: 'cc', target: `gen:${fb.name}:zoom`, min: 0.95, max: 1.05 }; onMidiMessage({ data: [0xb0, 1, 64] });
  onMidiMessage({ data: [0xc0, 0] }); out.pcIgnoredByDefault = app.layers[0].enabled === false;
  app.pcToScene = true; onMidiMessage({ data: [0xc0, 0] }); out.pcWorksWhenEnabled = app.layers[0].enabled === true;
  // undo delete
  const n = app.layers.length; await deleteLayer(app.layers[2].id); undoDelete();
  out.undoRestored = app.layers.length === n && app.layers[2].type === 'mask';
  // blackout
  toggleBlackout(true); const px = app.canvas.ctx.getImageData(10, 10, 1, 1).data; out.blackoutOn = app.blackout; toggleBlackout(false);
  updateLayerList(); updateOverlay();
  await saveAutosave();
  out.autosaveStored = !!(await idbGet('kv', 'autosave'));
  out.cacheHasImage = !!(await loadCachedMediaBlob('image', 'test-image.png'));
  out.cacheHasGif = !!(await loadCachedMediaBlob('gif', 'test-anim.gif'));
  return out;
}
"""

JS_PHYSICS_CHECK = """
() => {
  const P = app.layers.find(l => l.type === 'physics');
  const M = app.layers.find(l => l.type === 'mask');
  const w = app.canvas.logicalWidth, h = app.canvas.logicalHeight;
  const poly = M.points.map(p => ({x: pctToPx(p.x, w), y: pctToPx(p.y, h)}));
  const arena = P.points.map(p => ({x: pctToPx(p.x, w), y: pctToPx(p.y, h)}));
  const objs = P.physics.objects;
  return {
    inMask: objs.filter(o => pointInPolygon(pctToPx(o.x, w), pctToPx(o.y, h), poly)).length,
    outArena: objs.filter(o => !pointInPolygon(pctToPx(o.x, w), pctToPx(o.y, h), arena)).length,
    nan: objs.filter(o => !isFinite(o.x) || !isFinite(o.y) || !isFinite(o.vx)).length,
    count: objs.length
  };
}
"""

JS_SAVE = """
async () => {
  const snap = await buildProjectSnapshot(true);
  return JSON.stringify(snap);
}
"""

JS_LOAD_FROM_JSON = """
async (text) => {
  // Simulate fresh machine: wipe library + IDB cache, then load the self-contained file.
  app.layers = []; app.scenes = []; midi.ccMaps = [];
  app.mediaLibrary.forEach(stopMediaResources); app.mediaLibrary = [];
  const db = await idbOpen();
  await new Promise(r => { const tx = db.transaction('files', 'readwrite'); tx.objectStore('files').clear(); tx.oncomplete = r; });
  await restoreFromSnapshot(JSON.parse(text), 'Project loaded');
  await new Promise(r => setTimeout(r, 2500));
  showRelinkModalIfNeeded();
  const img = app.mediaLibrary.find(m => m.name === 'test-image.png');
  const gif = app.mediaLibrary.find(m => m.name === 'test-anim.gif');
  const P = app.layers.find(l => l.type === 'physics');
  return {
    layers: app.layers.length,
    imgRestored: !!(img && img.element && !img.needsRelink),
    gifRestored: !!(gif && gif.element && !gif.needsRelink),
    projLinked: app.layers.filter(l => l.type === 'projection' && l.mediaName).every(l => l.mediaId && app.mediaLibrary.some(m => m.id === l.mediaId)),
    fbLinked: !!app.layers.find(l => l.mediaName && l.mediaName.startsWith('Feedback')).mediaId,
    scenes: app.scenes.length, sceneNote: app.scenes[0].note, cc: midi.ccMaps.length,
    physObjs: P ? P.physics.objects.length : -1,
    relinkModalVisible: document.getElementById('loadProjectModal').classList.contains('visible'),
    pcToScene: app.pcToScene
  };
}
"""

JS_MOTIONCUT = """
async () => {
  // Static source must fade to black; a changed source must light up again.
  const mk = (color) => { const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'); x.fillStyle = color; x.fillRect(0,0,64,64); x.fillStyle = '#fff'; x.fillRect(16,16,32,32); return c; };
  const a = mk('#204080');
  const img = { id: uuid(), name: 'static-src', type: 'image', kind: 'image', element: a, width: 64, height: 64, filename: 'static-src', needsRelink: false };
  app.mediaLibrary.push(img);
  const cut = createGeneratorMedia('motioncut', { learn: 0.2, threshold: 0.16, soft: 0.05, hold: 0.5 }, null, 'cut-test');
  cut.sourceId = img.id; cut.sourceName = img.name; cut._preview = true; app.mediaLibrary.push(cut);
  const lum = () => { const c = document.createElement('canvas'); c.width = c.height = 32; const x = c.getContext('2d'); x.drawImage(cut.element, 0, 0, 32, 32); const d = x.getImageData(0,0,32,32).data; let s = 0; for (let i = 0; i < d.length; i += 4) s += d[i] + d[i+1] + d[i+2]; return s / (d.length / 4) / 3; };
  for (let i = 0; i < 60; i++) tickGenerator(cut, 1/60);
  const faded = lum();
  // Move the white square: those pixels differ from the learned background.
  const x = a.getContext('2d'); x.fillStyle = '#204080'; x.fillRect(0,0,64,64); x.fillStyle = '#fff'; x.fillRect(0,0,24,24);
  tickGenerator(cut, 1/60); tickGenerator(cut, 1/60);
  const lit = lum();
  // Filter: edges of a flat image are ~0, edges of the square's border are bright; invert flips luma
  const f = createGeneratorMedia('filter', { mode: 0, amount: 1, scale: 1, hue: 0 }, null, 'filt-test');
  f.sourceId = img.id; f.sourceName = img.name; f._preview = true; app.mediaLibrary.push(f);
  const lumF = () => { const gl = f._G.gl, n = f._G.res; const d = new Uint8Array(n * n * 4); gl.readPixels(0, 0, n, n, gl.RGBA, gl.UNSIGNED_BYTE, d); let s = 0; for (let i = 0; i < d.length; i += 4) s += d[i] + d[i+1] + d[i+2]; return s / (n * n) / 3; };
  tickGenerator(f, 0.016); const edgeL = lumF();
  f.params.mode = 5; tickGenerator(f, 0.016); const invL = lumF();
  // Hardness: a soft object has lower alpha at its rim than at its center; a hard one is opaque at both
  const P0 = app.layers.find(l => l.type === 'physics');
  const probe = (hard) => { const c = document.createElement('canvas'); c.width = c.height = 200; const x = c.getContext('2d'); const t = { id: 'p', kind: 'shape', shape: 'circle', enabled: true, alpha: 1, hardness: hard, x: 50, y: 50, r: 30, color: '#ff0000', rot: 0, rotV: 0, vx: 0, vy: 0 }; drawPhysicsObject(x, t, 200, 200); const center = x.getImageData(100, 100, 1, 1).data[3]; const rim = x.getImageData(100 + 56, 100, 1, 1).data[3]; return [center, rim]; };
  const hardP = probe(1), softP = probe(0.2);
  // Soft mask: render a filled canvas then a feathered mask layer; center cut, rim partially cut, outside untouched
  const maskProbe = (hard) => { const c = document.createElement('canvas'); c.width = c.height = 200; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0,0,200,200);
    const saveL = app.layers, saveW = app.canvas.logicalWidth, saveH = app.canvas.logicalHeight, saveCtx = app.canvas.ctx;
    app.layers = [{ id: 'm', type: 'mask', name: 'm', enabled: true, hardness: hard, points: [{x:20,y:20},{x:80,y:20},{x:80,y:80},{x:20,y:80}] }];
    app.canvas.ctx = x; app.canvas.logicalWidth = 200; app.canvas.logicalHeight = 200;
    x.fillStyle = '#fff'; // renderProjection clears to black; draw white under the mask by rendering, then sampling alpha is not possible on opaque ctx -> emulate the mask pass directly
    app.layers = saveL; app.canvas.ctx = saveCtx; app.canvas.logicalWidth = saveW; app.canvas.logicalHeight = saveH;
    const pts = [{x:40,y:40},{x:160,y:40},{x:160,y:160},{x:40,y:160}];
    const fillPoly = (cc) => { cc.fillStyle = '#000'; cc.beginPath(); pts.forEach((p,i) => i ? cc.lineTo(p.x,p.y) : cc.moveTo(p.x,p.y)); cc.closePath(); cc.fill(); };
    x.globalCompositeOperation = 'destination-out';
    if (hard < 0.995) drawSoft(x, { x: 40, y: 40, w: 120, h: 120, cx: 100, cy: 100, radius: 85 }, hard, fillPoly); else fillPoly(x);
    x.globalCompositeOperation = 'source-over';
    const a = (px, py) => x.getImageData(px, py, 1, 1).data[3];
    return [a(100,100), a(100,45), a(100,20)]; };
  const mHard = maskProbe(1), mSoft = maskProbe(0.2);
  // Edge fade: corners/edges go dark, center untouched; saved in settings
  const fadeProbe = (size, shape) => { const c = document.createElement('canvas'); c.width = 200; c.height = 100; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0,0,200,100); app.edgeFade = { size, shape, softness: 1 }; renderEdgeFade(x, 200, 100); const g = (px, py) => x.getImageData(px, py, 1, 1).data[0]; return [g(100, 50), g(2, 50), g(100, 2)]; };
  const fOff = fadeProbe(0, 'rect'), fRect = fadeProbe(0.3, 'rect'), fOval = fadeProbe(0.3, 'oval');
  // Projection quad fade border: center opaque, near the edge faded, in texture space
  const qc = document.createElement('canvas'); qc.width = qc.height = 200; const qx = qc.getContext('2d');
  const srcC = document.createElement('canvas'); srcC.width = srcC.height = 64; srcC.getContext('2d').fillStyle = '#fff'; srcC.getContext('2d').fillRect(0, 0, 64, 64);
  const qpts = [{x:20,y:20},{x:180,y:20},{x:180,y:180},{x:20,y:180}];
  renderQuadSoft(qx, srcC, qpts, 0.3);
  const qa = (px, py) => qx.getImageData(px, py, 1, 1).data[3];
  const quadFade = [qa(100, 100), qa(100, 24), qa(24, 24)];
  // seam check: alpha along a row inside the fade band must be smooth (no spikes where triangles met)
  const row = []; for (let px = 30; px < 170; px += 2) row.push(qa(px, 40));
  let maxJump = 0; for (let i = 1; i < row.length - 1; i++) maxJump = Math.max(maxJump, Math.abs(row[i] - (row[i - 1] + row[i + 1]) / 2));
  const quadFadeOk = quadFade[0] === 255 && quadFade[1] < 60 && quadFade[2] < 20 && maxJump <= 3;
  app.edgeFade = { size: 0.2, shape: 'oval', softness: 1 };
  const fadeSaved = (await buildProjectSnapshot(false)).settings.edgeFade.shape === 'oval';
  app.edgeFade = { size: 0, shape: 'rect', softness: 1 };
  const edgeFadeOk = fOff[0] === 255 && fOff[1] === 255 && fRect[0] === 255 && fRect[1] < 40 && fRect[2] < 40 && fOval[0] === 255 && fOval[1] < 200 && fadeSaved;
  const softMaskOk = mHard[0] === 0 && mHard[1] === 0 && mHard[2] === 255 && mSoft[0] === 0 && mSoft[1] > 60 && mSoft[1] < 255 && mSoft[2] === 255;
  const hardnessOk = hardP[0] > 250 && hardP[1] > 200 && softP[0] > 250 && softP[1] < 100;
  const o = P0.physics.objects[0]; o.alpha = 0.3;
  const sp = serializePhysics(app.layers.find(l => l.type === 'physics').physics).objects[0].alpha;
  o.alpha = 1;
  // Camera: stop/start toggles the inspector button text; stop twice is harmless; per-camera resolution saved
  let cam = app.mediaLibrary.find(m => m.kind === 'camera');
  const camId = cam.id;
  const prevSel = app.selectedLayerId; app.selectedLayerId = null; app.selectedObjectId = null;
  selectMedia(cam.id);
  const btnText = () => { const b = [...document.querySelectorAll('#inspectorBody button')].find(x => /camera/i.test(x.textContent) && !/switch/i.test(x.textContent)); return b ? b.textContent : ''; };
  const t1 = btnText(); killWebcam(cam.id); const t2 = btnText(); killWebcam(cam.id); const t3 = btnText();
  await startWebcam(camId); await new Promise(r => setTimeout(r, 300)); selectMedia(camId); const t4 = btnText();
  cam = app.mediaLibrary.find(m => m.id === camId);
  await setCameraResolution(cam, 640, 360);
  cam = app.mediaLibrary.find(m => m.id === camId);
  const savedCam = (await buildProjectSnapshot(false)).media.find(m => m.id === camId);
  const camState = { stopLabel: /Stop/.test(t1), startLabel: /Start/.test(t2) && /Start/.test(t3), backToStop: /Stop/.test(t4), resSaved: !!(savedCam.camRes && savedCam.camRes[0] === 640), hasDeviceId: !!cam.deviceId, oneEntry: app.mediaLibrary.filter(m => m.kind === 'camera').length === 1 };
  await setCameraResolution(cam, 0, 0);
  app.selectedLayerId = prevSel;
  // Quality switch: effect buffers resize in place, camera track asked for a new size, same ids
  const fb = app.mediaLibrary.find(m => m.gen === 'feedback'); const fbId = fb.id, r0 = fb.element.width;
  await applyQuality('low', { silent: true }); await new Promise(r => setTimeout(r, 400));
  const camEl = app.mediaLibrary.find(m => m.kind === 'camera').element;
  const lowRes = fb.element.width, camW = camEl ? camEl.videoWidth : 0;
  await applyQuality('med', { silent: true }); await new Promise(r => setTimeout(r, 400));
  const quality = { sameId: fb.id === fbId && app.mediaLibrary.some(m => m.id === fbId), lowRes, back: fb.element.width === r0, camW, settingsSaved: (await buildProjectSnapshot(false)).settings.quality === 'med' };
  app.mediaLibrary = app.mediaLibrary.filter(m => m !== img && m !== cut && m !== f);
  return { faded: +faded.toFixed(1), lit: +lit.toFixed(1), edgeL: +edgeL.toFixed(1), invL: +invL.toFixed(1), alphaSaved: sp === 0.3, quality, camState, hardnessOk, hardP, softP, softMaskOk, mHard, mSoft, edgeFadeOk, fOff, fRect, fOval, quadFadeOk, quadFade, maxJump };
}
"""

JS_UI_EXTRAS = """
() => {
  const out = {};
  const n0 = app.layers.length;
  const gif = app.mediaLibrary.find(m => m.name === 'test-anim.gif');
  const rect = app.canvas.element.getBoundingClientRect();
  // Drop media at stage center with a non-physics layer selected -> new projection quad of sensible size
  app.selectedLayerId = app.layers[0].id;
  placeMediaAt(gif, rect.left + rect.width * 0.5, rect.top + rect.height * 0.5);
  const L = app.layers[app.layers.length - 1];
  const w = L.points[1].x - L.points[0].x, h = L.points[3].y - L.points[0].y;
  out.placed = app.layers.length === n0 + 1 && L.type === 'projection' && L.mediaId === gif.id && w > 20 && w < 50 && h > 5;
  out.centered = Math.abs((L.points[0].x + w / 2) - 50) < 1;
  // Drop inside selected physics arena -> sprite, no new layer
  const P = app.layers.find(l => l.type === 'physics');
  app.selectedLayerId = P.id;
  const n1 = app.layers.length, o1 = P.physics.objects.length;
  placeMediaAt(gif, rect.left + rect.width * 0.7, rect.top + rect.height * 0.7);
  out.spriteDrop = app.layers.length === n1 && P.physics.objects.length === o1 + 1;
  // Reorder: move first layer above the last
  const a = app.layers[0].id, z = app.layers[app.layers.length - 1].id;
  reorderLayer(a, z, true);
  out.reordered = app.layers[app.layers.length - 1].id === a;
  reorderLayer(a, z, false);
  out.reorderedBack = app.layers[app.layers.length - 1].id === z && app.layers[app.layers.length - 2].id === a;
  // MIDI clear
  const fb = app.mediaLibrary.find(m => m.gen === 'feedback');
  midi.learn = { type: 'cc', target: `gen:${fb.name}:warp`, min: 0, max: 0.03 }; onMidiMessage({ data: [0xb0, 9, 1] });
  const bound = midi.ccMaps.some(m => m.cc === 9);
  midiClearParam(`gen:${fb.name}:warp`);
  out.ccCleared = bound && !midi.ccMaps.some(m => m.cc === 9);
  midiClearScene(app.scenes[0].id);
  out.noteCleared = app.scenes[0].note === null;
  midi.learn = { type: 'scene', sceneId: app.scenes[0].id }; onMidiMessage({ data: [0x90, 40, 100] });
  out.mapRows = document.querySelectorAll('#midiMapList .midi-row').length;
  out.sceneInSidebar = !!document.querySelector('#sidebar #sceneList .pad');
  return out;
}
"""

JS_GRAB = """
async () => {
  const out = {};
  const P = app.layers.find(l => l.type === 'physics');
  const o0 = P.physics.objects[0];
  const rect = app.canvas.element.getBoundingClientRect();
  const cx = rect.left + pctToPx(o0.x, rect.width), cy = rect.top + pctToPx(o0.y, rect.height);
  const mk = (type, x, y) => new PointerEvent(type, { clientX: x, clientY: y, button: 0, pointerId: 1, bubbles: true });
  app.canvas.element.dispatchEvent(mk('pointerdown', cx, cy));
  const o = grab.obj || o0; // topmost object under the pointer
  out.grabbed = !!o._held;
  // drag fast to the right over ~80ms, then let physics run a frame while held
  const dir = o.x > 50 ? -1 : 1; // drag toward the center so the arena wall does not interfere
  for (let i = 1; i <= 8; i++) { app.canvas.element.dispatchEvent(mk('pointermove', cx + dir * i * 25, cy)); await new Promise(r => setTimeout(r, 10)); }
  await new Promise(r => requestAnimationFrame(r));
  out.followed = Math.abs(pctToPx(o.x, rect.width) - (cx + dir * 200 - rect.left)) < 30;
  document.dispatchEvent(mk('pointerup', cx + dir * 200, cy));
  out.released = !o._held;
  out.thrownRight = o.vx * dir > 5; out.vx = Math.round(o.vx);
  // bump
  const before = P.physics.objects.map(x => Math.hypot(x.vx, x.vy));
  app.bumpKey = 'x';
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'x', bubbles: true }));
  const after = P.physics.objects.map(x => Math.hypot(x.vx, x.vy));
  out.bumped = after.some((v, i) => Math.abs(v - before[i]) > 1);
  const snap = await buildProjectSnapshot(false);
  out.bumpKeySaved = snap.settings.bumpKey === 'x';
  // Scene edits persist: change something while scene 1 active, switch to 2 and back
  recallScene(app.scenes[0].id);
  const nBefore = app.layers.length;
  app.layerType = 'mask'; createLayer(); app.layers[app.layers.length - 1].points = [{x:1,y:1},{x:9,y:1},{x:9,y:9}]; app.addingPoints = false;
  recallScene(app.scenes[1].id);
  recallScene(app.scenes[0].id);
  out.sceneEditKept = app.layers.length === nBefore + 1;
  await deleteLayer(app.layers[app.layers.length - 1].id);
  recallScene(app.scenes[1].id); recallScene(app.scenes[0].id);
  out.sceneDeleteKept = app.layers.length === nBefore;
  // duplicate scene as template: edit the copy, original untouched
  const s0 = app.scenes[0], nScenes = app.scenes.length;
  duplicateScene(s0.id);
  const copy = app.scenes[1];
  const ids = new Set(s0.layers.map(l => l.id));
  const plasma = app.mediaLibrary.find(m => m.gen === 'plasma');
  app.layers[0].mediaId = plasma.id; app.layers[0].mediaName = plasma.name;
  recallScene(s0.id);
  out.sceneDup = app.scenes.length === nScenes + 1 && copy.name === s0.name + ' copy' && copy.note === null
    && copy.layers.length === s0.layers.length && copy.layers.every(l => !ids.has(l.id))
    && app.scenes[1].layers[0].mediaName === plasma.name && app.layers[0].mediaName !== plasma.name;
  await deleteScene(copy.id);
  app.bumpKey = ' ';
  return out;
}
"""

JS_OBJECTS = """
async () => {
  const out = {};
  const P = app.layers.find(l => l.type === 'physics');
  selectLayer(P.id);
  out.childRows = document.querySelectorAll('#layerList .obj-item').length === P.physics.objects.length;
  const o = P.physics.objects[2];
  selectObject(P.id, o.id);
  out.selectedRow = !!document.querySelector(`#layerList .obj-item.selected[data-object-id="${o.id}"]`);
  out.inspectorObj = !!document.querySelector('#inspectorBody');
  await new Promise(r => requestAnimationFrame(r));
  out.handles = document.querySelectorAll('#physOverlay .obj-handle').length === P.physics.objects.length
    && document.querySelectorAll('#physOverlay .obj-handle.selected .handle').length === 2;
  // scale via handle drag: pointerdown on the scale handle, move far from center
  const rect = app.canvas.element.getBoundingClientRect();
  const cx = rect.left + pctToPx(o.x, rect.width), cy = rect.top + pctToPx(o.y, rect.height);
  const mk = (type, x, y) => new PointerEvent(type, { clientX: x, clientY: y, button: 0, pointerId: 2, bubbles: true });
  const sc = document.querySelector('#physOverlay .obj-handle.selected .handle.scale');
  const r0 = o.r;
  sc.dispatchEvent(mk('pointerdown', cx + 10, cy + 10));
  document.dispatchEvent(mk('pointermove', cx + 120, cy + 120));
  document.dispatchEvent(mk('pointerup', cx + 120, cy + 120));
  out.scaled = o.r > r0 + 3;
  // rotate
  await new Promise(r => requestAnimationFrame(r));
  const rh = document.querySelector('#physOverlay .obj-handle.selected .handle.rotate');
  const cx2 = rect.left + pctToPx(o.x, rect.width), cy2 = rect.top + pctToPx(o.y, rect.height); // object may have drifted
  rh.dispatchEvent(mk('pointerdown', cx2 + 10, cy2));
  document.dispatchEvent(mk('pointermove', cx2, cy2 + 100));
  document.dispatchEvent(mk('pointerup', cx2, cy2 + 100));
  out.rotated = Math.abs(o.rot - Math.PI / 2) < 0.1;
  // reorder objects: move first to top
  const first = P.physics.objects[0].id, last = P.physics.objects[P.physics.objects.length - 1].id;
  reorderObject(P.id, first, last, true);
  out.reordered = P.physics.objects[P.physics.objects.length - 1].id === first;
  // hide: not simulated, not drawn in overlay, survives save
  const hid = P.physics.objects[1];
  toggleObjectEnabled(P.id, hid.id);
  const hx = hid.x, hy = hid.y;
  await new Promise(r => setTimeout(r, 300));
  await new Promise(r => requestAnimationFrame(r));
  out.hiddenFrozen = hid.enabled === false && hid.x === hx && hid.y === hy;
  out.hiddenNoHandle = document.querySelectorAll('#physOverlay .obj-handle').length === P.physics.objects.length - 1;
  out.hiddenSaved = serializePhysics(P.physics).objects.find(x => x.id === hid.id).enabled === false;
  toggleObjectEnabled(P.id, hid.id);
  // delete via key
  const n = P.physics.objects.length;
  selectObject(P.id, o.id);
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Delete', bubbles: true }));
  await new Promise(r => setTimeout(r, 30));
  out.deleted = P.physics.objects.length === n - 1 && app.layers.includes(P);
  // drop media onto a brand-new physics layer that is still waiting for arena points
  app.layerType = 'physics'; createLayer();
  const NP = app.layers[app.layers.length - 1];
  out.wasAdding = app.addingPoints === true;
  const gif = app.mediaLibrary.find(m => m.name === 'test-anim.gif');
  placeMediaAt(gif, rect.left + rect.width * 0.5, rect.top + rect.height * 0.5);
  out.dropEndedArena = app.addingPoints === false && NP.physics.objects.length === 1 && app.layers.length === app.layers.indexOf(NP) + 1;
  await deleteLayer(NP.id);
  return out;
}
"""

JS_MODAL_YT = """
async () => {
  const out = {};
  // Real modal: cancel keeps the layer, OK deletes; one shared widget
  confirmAction = window._realConfirm;
  const n = app.layers.length;
  const pr = deleteLayer(app.layers[0].id);
  await new Promise(r => setTimeout(r, 30));
  out.modalShown = document.getElementById('confirmModal').classList.contains('visible') && document.getElementById('confirmTitle').textContent.startsWith('Delete ');
  document.getElementById('confirmCancelBtn').click(); await pr;
  out.cancelKept = app.layers.length === n;
  const pr2 = deleteObject(app.layers.find(l => l.type === 'physics').id, app.layers.find(l => l.type === 'physics').physics.objects[0].id);
  await new Promise(r => setTimeout(r, 30));
  out.sameWidget = document.getElementById('confirmModal').classList.contains('visible');
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); await pr2;
  out.escCancels = !document.getElementById('confirmModal').classList.contains('visible');
  out.modalCount = document.querySelectorAll('#confirmModal').length === 1;
  confirmAction = async () => true;
  // YouTube
  out.parse = parseYouTubeId('https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=5') === 'dQw4w9WgXcQ' && parseYouTubeId('https://youtu.be/abcdefghijk') === 'abcdefghijk' && parseYouTubeId('https://example.com/x.mp4') === null;
  const yt = createYouTubeMedia('dQw4w9WgXcQ'); upsertMedia(yt); updateMediaList();
  app.layerType = 'projection'; createLayer(); const L = app.layers[app.layers.length - 1];
  L.points = [{x:10,y:10},{x:60,y:15},{x:55,y:60},{x:12,y:50}]; L.mediaId = yt.id; L.mediaName = yt.name; app.addingPoints = false;
  await new Promise(r => requestAnimationFrame(r)); await new Promise(r => requestAnimationFrame(r));
  const fr = document.querySelector(`#domLayers iframe[data-layer-id="${L.id}"]`);
  out.iframe = !!fr && fr.src.includes('dQw4w9WgXcQ') && fr.style.transform.startsWith('matrix3d(');
  // homography maps iframe corners onto the quad
  const m = fr.style.transform.match(/matrix3d\(([^)]+)\)/)[1].split(',').map(Number);
  const w = app.canvas.logicalWidth, h = app.canvas.logicalHeight;
  const apply = (x, y) => { const X = m[0]*x + m[4]*y + m[12], Y = m[1]*x + m[5]*y + m[13], W = m[3]*x + m[7]*y + m[15]; return [X/W, Y/W]; };
  const [bx, by] = apply(640, 360); const br = L.points[2];
  out.homography = Math.abs(bx - pctToPx(br.x, w)) < 1 && Math.abs(by - pctToPx(br.y, h)) < 1;
  toggleBlackout(true); await new Promise(r => requestAnimationFrame(r)); out.blackoutHides = document.querySelectorAll('#domLayers iframe').length === 0; toggleBlackout(false);
  const snap = await buildProjectSnapshot(true);
  const e = snap.media.find(x => x.id === yt.id);
  out.serialized = e && e.kind === 'youtube' && e.videoId === 'dQw4w9WgXcQ' && !e.data;
  // swap URL in place: same id, layer still points at it, iframe follows
  const idBefore = yt.id;
  updateUrlMedia(yt, 'https://youtu.be/jNQXAC9IVRw');
  await new Promise(r => requestAnimationFrame(r)); await new Promise(r => requestAnimationFrame(r));
  const fr2 = document.querySelector(`#domLayers iframe[data-layer-id="${L.id}"]`);
  out.urlSwap = yt.id === idBefore && yt.videoId === 'jNQXAC9IVRw' && L.mediaId === yt.id && !!fr2 && fr2.src.includes('jNQXAC9IVRw');
  updateUrlMedia(yt, 'https://example.com/clip.mp4');
  out.urlToVideo = yt.id === idBefore && yt.kind === 'video' && yt.remote === true && !!yt.element && L.mediaId === yt.id;
  // effect chain on a layer: wrap gif with reaction, then kaleido; two instances have independent params; unwrap
  const gifL = app.layers.find(l => l.type === 'projection' && l.mediaName === 'test-image.png') || app.layers[0];
  const baseId = gifL.mediaId;
  addEffectToLayer(gifL.id, 'reaction');
  const fx1 = app.mediaLibrary.find(m => m.id === gifL.mediaId);
  addEffectToLayer(gifL.id, 'kaleido');
  const fx2 = app.mediaLibrary.find(m => m.id === gifL.mediaId);
  out.chain = fx1.gen === 'reaction' && fx1.sourceId === baseId && fx2.gen === 'kaleido' && fx2.sourceId === fx1.id;
  const other = app.layers.find(l => l.type === 'projection' && l.id !== gifL.id && l.id !== L.id && l.mediaId);
  addEffectToLayer(other.id, 'reaction');
  const fx3 = app.mediaLibrary.find(m => m.id === other.mediaId);
  fx3.params.feed = 0.08;
  out.independent = fx3.id !== fx1.id && fx1.params.feed !== 0.08;
  removeEffectFromLayer(gifL.id); removeEffectFromLayer(gifL.id);
  out.unwrapped = gifL.mediaId === baseId;
  // inspector: visible add-effect button opens a list; clicking an item stacks it
  selectLayer(gifL.id);
  const addBtn = document.querySelector('#inspectorBody .stack-add');
  out.addBtnVisible = !!addBtn && addBtn.offsetHeight > 0;
  addBtn.click();
  const item = document.querySelector('#inspectorBody .stack-add-wrap.open .stack-add-item');
  out.menuOpens = !!item;
  item.click();
  const fx4 = app.mediaLibrary.find(m => m.id === gifL.mediaId);
  out.menuAdds = !!fx4 && GENERATORS[fx4.gen].effect && fx4.sourceId === baseId;
  removeEffectFromLayer(gifL.id); app.mediaLibrary = app.mediaLibrary.filter(m => m.id !== fx4.id);
  // UI scale persisted
  // Fullscreen panels overlay: with .fs, showing panels must not change the stage size
  const appEl = document.getElementById('app'); appEl.classList.add('fs');
  Object.defineProperty(document, 'fullscreenElement', { configurable: true, get: () => document.documentElement });
  window.dispatchEvent(new Event('resize')); await new Promise(r => requestAnimationFrame(r));
  const w0 = app.canvas.logicalWidth, h0 = app.canvas.logicalHeight;
  togglePanels(true); window.dispatchEvent(new Event('resize')); await new Promise(r => requestAnimationFrame(r));
  const sb = document.getElementById('sidebar').getBoundingClientRect();
  out.fsPanels = appEl.classList.contains('panels') && sb.width > 100 && app.canvas.logicalWidth === w0 && app.canvas.logicalHeight === h0 && w0 >= window.innerWidth - 2;
  togglePanels(false); appEl.classList.remove('fs'); delete document.fullscreenElement; Object.defineProperty(document, 'fullscreenElement', { configurable: true, get: () => null });
  window.dispatchEvent(new Event('resize')); await new Promise(r => requestAnimationFrame(r));
  applyUiScale(1.3); out.uiScale = localStorage.getItem('gm_ui_scale') === '1.3' && getComputedStyle(document.documentElement).getPropertyValue('--ui-scale').trim() === '1.3';
  applyUiScale(1);
  removeEffectFromLayer(other.id);
  for (const f of [fx1, fx2, fx3]) { app.mediaLibrary = app.mediaLibrary.filter(m => m.id !== f.id); }
  await deleteLayer(L.id); await removeMedia(yt);
  return out;
}
"""

JS_SCALE = """
() => {
  const out = {};
  const near = (a, b, tol) => Math.abs(a - b) <= (tol || 0.01);
  // length parsing in inches
  out.parse = near(parseLen("8'", 'ft'), 96) && near(parseLen("8' 6\\"", 'ft'), 102) && near(parseLen('8ft 6in', 'ft'), 102) && near(parseLen('96"', 'ft'), 96)
    && near(parseLen('2.54m', 'ft'), 100, 0.01) && near(parseLen('254cm', 'ft'), 100, 0.01) && near(parseLen('12', 'in'), 12) && near(parseLen('8', 'ft'), 96) && isNaN(parseLen('abc', 'ft'));
  out.fmt = fmtLen(102, 'ft') === "8'6\\"" && fmtLen(96, 'in') === '96"' && fmtLen(100, 'cm') === '254.0 cm' && fmtLen(39.3700787, 'm') === '1.00 m';
  // measure a ruler: two points 50% of the width apart, say they are 10 ft -> wall is 20 ft wide
  startMeasure();
  const rect = app.canvas.element.getBoundingClientRect();
  onCanvasClick({ clientX: rect.left + rect.width * 0.25, clientY: rect.top + rect.height * 0.5 });
  onCanvasClick({ clientX: rect.left + rect.width * 0.75, clientY: rect.top + rect.height * 0.5 });
  out.hintInput = document.getElementById('stageHintInput').style.display !== 'none';
  finishMeasure("10'");
  out.wall = near(app.scale.wallWidthIn, 240, 0.5) && !app.measuring && !!app.scale.ruler;
  // set a projection quad to 8 ft tall, aspect kept
  const L = app.layers.find(l => l.type === 'projection' && l.points.length === 4);
  app.selectedLayerId = L.id; renderInspector();
  { const cc = getLayerCenter(L); moveLayerBy(L, 50 - cc.x, 50 - cc.y); } // park it mid-stage so nothing clips
  const before = layerSizeIn(L), ratio = before.w / before.h;
  setLayerSizeIn(L, 'h', 96);
  const after = layerSizeIn(L);
  out.height8ft = near(after.h, 96, 0.5) && near(after.w / after.h, ratio, 0.02);
  // the inspector shows the real size and the overlay label too
  out.inspectorRows = !!document.querySelector('.geometry input.len') && document.querySelector('.ctx .summary').textContent.length > 0;
  out.label = Array.from(document.querySelectorAll('#svgOverlay .size-label')).some(t => t.textContent.includes("8'"));
  // nudge by 1 ft with arrow keys
  app.scale.nudgeIn = 12;
  const c0 = getLayerCenter(L);
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
  const c1 = getLayerCenter(L);
  out.nudge = near(pctXToIn(c1.x - c0.x), 12, 0.2);
  // realign: move both ruler ends 10% right -> scene translates by 10% when rulerMovesScene is on
  app.scale.rulerMovesScene = true;
  const p0 = L.points.map(p => ({ ...p }));
  app.dragging = { active: true, type: 'ruler', pointIndex: 0, startRuler: app.scale.ruler.map(p => ({ ...p })) };
  moveRulerEnd(0, app.scale.ruler[0].x + 10, app.scale.ruler[0].y);
  app.dragging = { active: true, type: 'ruler', pointIndex: 1, startRuler: app.scale.ruler.map(p => ({ ...p })) };
  moveRulerEnd(1, app.scale.ruler[1].x + 10, app.scale.ruler[1].y);
  app.dragging.active = false;
  out.realign = L.points.every((p, i) => near(p.x, p0[i].x + 10, 0.05) && near(p.y, p0[i].y, 0.05)) && near(app.scale.wallWidthIn, 240, 0.5);
  app.scale.rulerMovesScene = false;
  return out;
}
"""

JS_STREAM = """
async (port) => { // port is a SECOND server: cross-origin, so CORS headers matter like in the field
  const out = {};
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  // URL heuristics
  out.hint = looksLikeMjpeg('http://phone:8080/video') && looksLikeMjpeg('http://pi:8080/?action=stream') && looksLikeMjpeg('http://cam/x.mjpg') && looksLikeMjpeg('http://x/whatever#mjpeg') && !looksLikeMjpeg('http://x/clip.mp4');
  // live stream with CORS -> readable by effects
  const m = createMjpegMedia(`http://127.0.0.1:${port}/test.mjpg?cors=1&frames=400`, null, 'cam-cors');
  upsertMedia(m); updateMediaList();
  for (let i = 0; i < 40 && !m.element; i++) await sleep(100);
  out.live = !!m.element && m.width === 64 && m.height === 48 && m.kind === 'stream' && m._cors === true;
  // frames change: the watchdog signature must move
  const sigs = new Set(); for (let i = 0; i < 12; i++) { await sleep(250); sigs.add(m._lastSig); }
  sigs.delete(null); out.animates = sigs.size >= 2;
  // on a quad: red or blue lands on the canvas
  const L = app.layers.find(l => l.type === 'projection' && l.points.length === 4);
  const keep = L.mediaId, keepName = L.mediaName; L.mediaId = m.id; L.mediaName = m.name;
  { const cc = getLayerCenter(L); moveLayerBy(L, 50 - cc.x, 50 - cc.y); }
  await sleep(300);
  const px = app.canvas.ctx.getImageData(Math.round(app.canvas.logicalWidth / 2), Math.round(app.canvas.logicalHeight / 2), 1, 1).data;
  out.drawn = (px[0] > 200 && px[2] < 60) || (px[2] > 200 && px[0] < 60);
  // effect can read it (CORS): a Filter in invert mode over red/blue gives cyan/yellow, i.e. green channel high
  addEffectToLayer(L.id, 'filter');
  const fx = app.mediaLibrary.find(x => x.id === L.mediaId); fx.params.mode = 5; fx.params.amount = 1; // full invert
  await sleep(500);
  const p2 = app.canvas.ctx.getImageData(Math.round(app.canvas.logicalWidth / 2), Math.round(app.canvas.logicalHeight / 2), 1, 1).data;
  out.effect = p2[1] > 150;
  removeStage((mm) => { L.mediaId = mm ? mm.id : null; }, fx, fx.id);
  // stream that ends -> watchdog reconnects (frames=12 means ~1.2 s of video, then a frozen frame)
  const m2 = createMjpegMedia(`http://127.0.0.1:${port}/test.mjpg?frames=12`, null, 'cam-short');
  upsertMedia(m2);
  for (let i = 0; i < 40 && !m2.element; i++) await sleep(100);
  const first = m2.element;
  out.noCorsFallback = m2._cors === false && !!first; // no header -> crossOrigin retry path
  for (let i = 0; i < 120 && m2.element === first; i++) await sleep(100);
  out.reconnected = m2.element !== first && !!m2.element;
  // serialize / restore keeps kind + url
  const snap = await buildProjectSnapshot(false);
  const e = snap.media.find(x => x.id === m.id);
  out.serialized = e && e.kind === 'stream' && e.remote === true && e.url === m.url && !e.data;
  // bad video URL falls back to a stream attempt
  const v = createRemoteVideoMedia(`http://127.0.0.1:${port}/test.mjpg?frames=50`, null, 'cam-as-video');
  upsertMedia(v);
  for (let i = 0; i < 60 && v.kind !== 'stream'; i++) await sleep(100);
  for (let i = 0; i < 40 && !v.element; i++) await sleep(100);
  out.videoFallback = v.kind === 'stream' && !!v.element;
  // cleanup
  L.mediaId = keep; L.mediaName = keepName;
  [m, m2, v].forEach(x => { stopMediaResources(x); app.mediaLibrary = app.mediaLibrary.filter(y => y.id !== x.id); });
  updateMediaList();
  return out;
}
"""

JS_UNDO = """
() => {
  const out = {};
  const L = app.layers.find(l => l.type === 'projection' && l.points.length === 4);
  app.selectedLayerId = L.id; app.selectedObjectId = null;
  const p0 = JSON.stringify(L.points);
  // move via nudge, undo brings points back, redo re-applies
  app.scale.nudgeIn = 12; nudgeSelected(1, 0, 1); nudgeSelected(1, 0, 1); // coalesced into one step
  const p1 = JSON.stringify(L.points);
  undo();
  const Lb = app.layers.find(l => l.id === L.id);
  out.undoMove = JSON.stringify(Lb.points) === p0 && p1 !== p0;
  redo();
  out.redoMove = JSON.stringify(app.layers.find(l => l.id === L.id).points) === p1;
  // drag start pushes; a simulated point drag then undo
  const rect = app.canvas.element.getBoundingClientRect();
  startDragPoint({ stopPropagation(){}, preventDefault(){}, clientX: rect.left, clientY: rect.top }, L.id, 0);
  onMouseMove({ clientX: rect.left + rect.width * 0.5, clientY: rect.top + rect.height * 0.5 }); onMouseUp();
  const moved = JSON.stringify(app.layers.find(l => l.id === L.id).points) !== p1;
  undo();
  out.undoPoint = moved && JSON.stringify(app.layers.find(l => l.id === L.id).points) === p1;
  // reorder + rotate undo
  const order0 = app.layers.map(l => l.id).join();
  moveLayerUp(app.layers[app.layers.length - 1].id); rotateLayer90(L.id);
  undo(); undo();
  out.undoReorderRotate = app.layers.map(l => l.id).join() === order0 && JSON.stringify(app.layers.find(l => l.id === L.id).points) === p1;
  // delete object then undo
  const P = app.layers.find(l => l.type === 'physics'); const n = P.physics.objects.length;
  const oid = P.physics.objects[0].id;
  P.physics.objects = P.physics.objects.filter(o => o.id !== oid); // deleteObject is async+confirm; emulate its pushUndo path
  pushUndo('delete object'); P.physics.objects.push({ id: 'junk', kind: 'shape', shape: 'circle', x: 1, y: 1, r: 2, rot: 0, rotV: 0, vx: 0, vy: 0, color: '#fff' });
  undo();
  out.undoObject = app.layers.find(l => l.type === 'physics').physics.objects.length === n - 1 && !app.layers.find(l => l.type === 'physics').physics.objects.some(o => o.id === 'junk');
  // stack cleared on scene recall and on snapshot restore: nothing stale comes back
  pushUndo('x'); recallScene(app.scenes[0].id);
  out.clearedOnScene = undoStack.length === 0 && redoStack.length === 0;
  // depth cap
  for (let i = 0; i < 25; i++) pushUndo('n' + i);
  out.depth = undoStack.length === TUNING.undoDepth;
  clearUndo();
  return out;
}
"""

JS_AUTOSAVE_RESTORE = """
async () => {
  // Autosave path: snapshot has no embedded data; media must come back from IDB cache.
  await saveAutosave();
  app.layers = []; app.mediaLibrary.forEach(stopMediaResources); app.mediaLibrary = [];
  const snap = await idbGet('kv', 'autosave');
  const hasData = (snap.media || []).some(m => m.data);
  await restoreFromSnapshot(snap);
  await new Promise(r => setTimeout(r, 2500));
  const img = app.mediaLibrary.find(m => m.name === 'test-image.png');
  const gif = app.mediaLibrary.find(m => m.name === 'test-anim.gif');
  return { hasEmbeddedData: hasData, imgFromCache: !!(img && img.element && !img.needsRelink), gifFromCache: !!(gif && gif.element && !gif.needsRelink), layers: app.layers.length };
}
"""


def main():
    httpd = serve()
    httpd2 = serve(PORT + 1)  # cross-origin host for stream tests
    url = f"http://127.0.0.1:{PORT}/index.html"
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=[
            "--no-sandbox", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "404" not in m.text and "example.com" not in m.text and "ERR_FAILED" not in m.text and "blocked by CORS policy" not in m.text else None)  # CORS probe on streams is intentional
        page.goto(url)
        page.wait_for_timeout(800)
        page.evaluate("async () => { const db = await idbOpen(); for (const s of ['kv','files']) await new Promise(r => { const tx = db.transaction(s,'readwrite'); tx.objectStore(s).clear(); tx.oncomplete = r; }); }")

        s = page.evaluate(JS_SETUP)
        check("webcam live", s["cam"])
        check("image + gif load via unified loader", s["imgLoaded"] and s["gifLoaded"])
        check("C4 unique pattern names", s["uniqueNames"] and s["plasma2Survived"], json.dumps({"survived": s["plasma2Survived"]}))
        check("W7 physics object cap", s["objectCap"] == 40, f"count={s['objectCap']}")
        check("W9 program change opt-in", s["pcIgnoredByDefault"] and s["pcWorksWhenEnabled"])
        check("W3 undo delete", s["undoRestored"])
        check("W2 blackout flag", s["blackoutOn"])
        check("C3 autosave in IndexedDB", s["autosaveStored"])
        check("C3 media blobs cached", s["cacheHasImage"] and s["cacheHasGif"])

        page.wait_for_timeout(2500)
        ph = page.evaluate(JS_PHYSICS_CHECK)
        check("physics avoids masks / stays in arena / no NaN", ph["inMask"] == 0 and ph["outArena"] == 0 and ph["nan"] == 0, json.dumps(ph))
        page.screenshot(path=str(SHOTS / "scene.png"))

        fps = page.evaluate("() => new Promise(r => { let n=0; const t0=performance.now(); const f=()=>{n++; if(performance.now()-t0<2000) requestAnimationFrame(f); else r(n/2);}; requestAnimationFrame(f); })")
        print(f"[INFO] fps (software GL, 12 objects): {fps:.0f}")

        ux = page.evaluate(JS_UI_EXTRAS)
        check("drag-drop media onto stage places sized quad / sprite", ux["placed"] and ux["centered"] and ux["spriteDrop"], json.dumps(ux))
        check("drag-reorder layers", ux["reordered"] and ux["reorderedBack"])
        check("MIDI learn + clear, map list, scenes in sidebar", ux["ccCleared"] and ux["noteCleared"] and ux["mapRows"] >= 2 and ux["sceneInSidebar"], json.dumps(ux))

        g = page.evaluate(JS_GRAB)
        check("grab, drag, throw physics object + bump hotkey", g["grabbed"] and g["followed"] and g["released"] and g["thrownRight"] and g["bumped"] and g["bumpKeySaved"] and g["sceneEditKept"] and g["sceneDeleteKept"] and g["sceneDup"], json.dumps(g))

        ob = page.evaluate(JS_OBJECTS)
        check("physics objects: rows, handles, scale, rotate, reorder, delete, drop into new layer", all(v is True for k, v in ob.items()), json.dumps(ob))

        my = page.evaluate(JS_MODAL_YT)
        check("confirm modal (single widget, cancel/esc) + YouTube layer (iframe, homography, serialize) + fs panels overlay", all(v is True for v in my.values()), json.dumps(my))

        mc = page.evaluate(JS_MOTIONCUT)
        check("Motion Cut fades static pixels, lights moved ones", mc["faded"] < 8 and mc["lit"] > mc["faded"] + 20, json.dumps(mc))
        check("Filter effect renders (edges sparse, invert bright) + object opacity saved", 2 < mc["edgeL"] < 120 and mc["invL"] > 100 and mc["alphaSaved"], json.dumps(mc))
        check("Hardness feathers object rim (center opaque, rim fades)", mc["hardnessOk"], json.dumps({"hard": mc["hardP"], "soft": mc["softP"]}))
        check("Soft mask: full cut inside, feathered rim, outside intact", mc["softMaskOk"], json.dumps({"hard": mc["mHard"], "soft": mc["mSoft"]}))
        check("Stage edge fade darkens edges, keeps center, persists", mc["edgeFadeOk"], json.dumps({"off": mc["fOff"], "rect": mc["fRect"], "oval": mc["fOval"]}))
        check("Projection quad fade border, seamless", mc["quadFadeOk"], json.dumps({"samples": mc["quadFade"], "maxSeamJump": mc["maxJump"]}))
        cs = mc["camState"]
        check("camera stop/start state + per-camera resolution", cs["stopLabel"] and cs["startLabel"] and cs["backToStop"] and cs["resSaved"] and cs["hasDeviceId"] and cs["oneEntry"], json.dumps(cs))
        q = mc["quality"]
        check("Quality switch resizes effects live (same id) and camera track", q["sameId"] and q["lowRes"] == 256 and q["back"] and q["settingsSaved"] and q["camW"] > 0, json.dumps(q))  # fake device ignores applyConstraints; real cams resize

        un = page.evaluate(JS_UNDO)
        check("Undo/redo: move, point drag, reorder, rotate, object, cleared on scene, depth", all(v is True for v in un.values()), json.dumps(un))

        sc = page.evaluate(JS_SCALE)
        check("Scale: parse/format lengths, measure ruler, 8 ft tall quad, nudge, ruler realign", all(v is True for v in sc.values()), json.dumps(sc))

        st = page.evaluate(JS_STREAM, PORT + 1)
        check("MJPEG stream: detect, play, draw, feed effects (CORS), no-CORS fallback, stall reconnect, serialize, video fallback", all(v is True for v in st.values()), json.dumps(st))

        a = page.evaluate(JS_AUTOSAVE_RESTORE)
        check("C3 autosave restores gif/image from cache without embedding", (not a["hasEmbeddedData"]) and a["imgFromCache"] and a["gifFromCache"], json.dumps(a))

        text = page.evaluate(JS_SAVE)
        size_mb = len(text) / 1048576
        has_data = '"data":"data:image/png' in text and '"data":"data:image/gif' in text
        check("C2 Save embeds image and gif data", has_data, f"{size_mb:.2f} MB")
        r = page.evaluate(JS_LOAD_FROM_JSON, text)
        check("C2 Load on fresh machine restores everything, no relink modal",
              r["imgRestored"] and r["gifRestored"] and r["projLinked"] and r["fbLinked"] and r["scenes"] == 2
              and r["sceneNote"] == 40 and r["cc"] == 1 and r["physObjs"] == 12 and not r["relinkModalVisible"] and r["pcToScene"],
              json.dumps(r))
        check("Scale survives Save/Load", page.evaluate("() => Math.abs(app.scale.wallWidthIn - 240) < 0.5 && !!app.scale.ruler && app.scale.rulerIn === 120"))
        check("Undo stack cleared by Load", page.evaluate("() => undoStack.length === 0 && redoStack.length === 0"))
        page.screenshot(path=str(SHOTS / "after-load.png"))

        check("no page errors", not errors, json.dumps(errors[:5]))
        browser.close()
    httpd.shutdown()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILED: {FAILS}")
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
