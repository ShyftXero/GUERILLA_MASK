"""
Headless tests for the structured-light mapping core (the pure CV/math).

Run:  ./tests/run_sl.sh        (needs uv; uses system Chrome at /usr/bin/google-chrome or $CHROME)

These exercise the camera<->projector homography and the difference-mask pipeline
(Otsu threshold, morphology, contour trace, polygon simplify) in isolation, loaded
from index.html. Webcam/UI glue is verified separately.
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
PORT = int(os.environ.get("GM_SL_TEST_PORT", "8779"))
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not cond:
        FAILS.append(name)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(port=PORT):
    os.chdir(ROOT)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# Camera<->projector homography: solve from 4 point-pairs, apply, invert.
JS_HOMOGRAPHY = """
() => {
  const out = {};
  // A known projective map M (not affine: last row has perspective terms).
  // M = [[2,0,5],[0.3,1.5,8],[0.002,0.001,1]]
  const T = (x, y) => {
    const w = 0.002*x + 0.001*y + 1;
    return { x: (2*x + 0*y + 5) / w, y: (0.3*x + 1.5*y + 8) / w };
  };
  const src = [{x:0,y:0},{x:100,y:0},{x:100,y:100},{x:0,y:100}];
  const dst = src.map(p => T(p.x, p.y));
  const H = slSolveHomography(src, dst);
  out.solved = Array.isArray(H) && H.length === 9;
  // 1. The 4 fitted corners must reproduce exactly.
  out.cornersOk = src.every((p, i) => {
    const q = slApplyHomography(H, p.x, p.y);
    return Math.hypot(q.x - dst[i].x, q.y - dst[i].y) < 1e-3;
  });
  // 2. An INDEPENDENT interior point must match the TRUE map M -> proves recovery, not mere fit.
  const ip = { x: 37, y: 61 };
  const q = slApplyHomography(H, ip.x, ip.y);
  const e = T(ip.x, ip.y);
  out.interiorOk = Math.hypot(q.x - e.x, q.y - e.y) < 1e-2;
  // 3. The inverse must round-trip a point back to itself.
  const Hi = slInvertHomography(H);
  const back = slApplyHomography(Hi, q.x, q.y);
  out.invertOk = Math.hypot(back.x - ip.x, back.y - ip.y) < 1e-2;
  // 4. Degenerate (collinear) input returns null, not garbage.
  const bad = slSolveHomography(
    [{x:0,y:0},{x:1,y:1},{x:2,y:2},{x:3,y:3}],
    [{x:0,y:0},{x:1,y:0},{x:2,y:0},{x:3,y:0}]);
  out.degenerateNull = bad === null;
  return out;
}
"""


# Difference-mask pipeline: diff-luma -> Otsu -> morphology -> contour -> simplify.
JS_PIPELINE = """
() => {
  const out = {};
  const w = 32, h = 32;
  // A 12x12 object at [10,22). Under black projection it's dark; under white it's
  // bright. Background stays dim either way (ambient). Diff should isolate the object.
  const mkFrame = (objVal, bgVal) => {
    const d = new Uint8ClampedArray(w * h * 4);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const inObj = x >= 10 && x < 22 && y >= 10 && y < 22;
      const v = inObj ? objVal : bgVal;
      const i = (y * w + x) * 4; d[i] = d[i+1] = d[i+2] = v; d[i+3] = 255;
    }
    return d;
  };
  const black = mkFrame(20, 15), white = mkFrame(230, 40);

  // 1. Luminance difference: object ~210, background ~25.
  const gray = slDiffLuma(white, black, w, h);
  const at = (x, y) => gray[y * w + x];
  out.diffLen = gray.length === w * h;
  out.diffObject = at(15, 15) > 150;
  out.diffBg = at(2, 2) < 60;

  // 2. Otsu threshold separates background from object (bg <= t < object).
  const t = slOtsu(gray, w * h);
  out.otsu = at(2, 2) <= t && at(15, 15) > t;

  // 3. Threshold to binary (strict: pixels above the threshold are foreground).
  const bin = new Uint8Array(w * h);
  for (let k = 0; k < w * h; k++) bin[k] = gray[k] > t ? 1 : 0;
  out.binObj = bin[15 * w + 15] === 1 && bin[2 * w + 2] === 0;

  // 4. Morphology (open then close) kills a stray speckle, fills a pinhole, keeps the blob.
  bin[0] = 1;                 // isolated speckle in the corner
  bin[16 * w + 16] = 0;       // pinhole inside the object
  const clean = slMorphOpenClose(bin, w, h, 1);
  out.speckleGone = clean[0] === 0;
  out.holeFilled = clean[16 * w + 16] === 1;
  out.blobKept = clean[11 * w + 11] === 1 && clean[20 * w + 20] === 1;

  // 5. Contour trace of the largest blob wraps the square.
  const contour = slTraceContour(clean, w, h);
  out.contourClosed = contour.length >= 8;
  const xs = contour.map(p => p.x), ys = contour.map(p => p.y);
  out.contourBounds = Math.min(...xs) <= 10 && Math.max(...xs) >= 21 && Math.min(...ys) <= 10 && Math.max(...ys) >= 21;

  // 6. Douglas-Peucker collapses the dense perimeter to a few corners, bounds preserved.
  const simp = slSimplifyPolygon(contour, 1.5);
  out.simpFew = simp.length >= 4 && simp.length <= 8;
  const sxs = simp.map(p => p.x), sys = simp.map(p => p.y);
  out.simpBounds = Math.min(...sxs) <= 11 && Math.max(...sxs) >= 20 && Math.min(...sys) <= 11 && Math.max(...sys) >= 20;
  return out;
}
"""


# End-to-end detector: capture -> silhouette polygon in canvas-% (via H_cp).
JS_DETECT = """
() => {
  const out = {};
  const camW = 48, camH = 36;
  const mkFrame = (objVal, bgVal) => {
    const d = new Uint8ClampedArray(camW * camH * 4);
    for (let y = 0; y < camH; y++) for (let x = 0; x < camW; x++) {
      const inObj = x >= 12 && x < 36 && y >= 9 && y < 27;
      const v = inObj ? objVal : bgVal;
      const i = (y * camW + x) * 4; d[i] = d[i+1] = d[i+2] = v; d[i+3] = 255;
    }
    return d;
  };
  const black = mkFrame(20, 15), white = mkFrame(230, 40);
  // H_cp maps camera pixels -> canvas %: the whole camera frame spans the whole canvas.
  const Hcp = slSolveHomography(
    [{x:0,y:0},{x:camW,y:0},{x:camW,y:camH},{x:0,y:camH}],
    [{x:0,y:0},{x:100,y:0},{x:100,y:100},{x:0,y:100}]);

  const pts = slSilhouettePct(white, black, camW, camH, Hcp, { simplifyEps: 2 });
  out.got = Array.isArray(pts) && pts.length >= 4 && pts.length <= 10;
  const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
  out.inRange = pts.every(p => p.x >= -1 && p.x <= 101 && p.y >= -1 && p.y <= 101);
  // object camera [12,36)x[9,27) -> roughly x in [25,75]%, y in [25,75]%
  out.boundsX = Math.min(...xs) < 30 && Math.max(...xs) > 70;
  out.boundsY = Math.min(...ys) < 30 && Math.max(...ys) > 70;
  // Identical frames (nothing lit) -> null, not an empty or garbage polygon.
  out.emptyNull = slSilhouettePct(mkFrame(15,15), mkFrame(15,15), camW, camH, Hcp, {}) === null;
  return out;
}
"""


# Stateful glue: store calibration, build + commit a mask layer, survive save/load.
JS_GLUE = """
async () => {
  const out = {};
  const camPts  = [{x:0,y:0},{x:48,y:0},{x:48,y:36},{x:0,y:36}];
  const projPts = [{x:0,y:0},{x:100,y:0},{x:100,y:100},{x:0,y:100}];

  // Calibration: store H_cp; the camera-centre maps to the canvas centre.
  out.calibSet = slSetCalibration(camPts, projPts) === true;
  out.hcpStored = Array.isArray(app.sl.Hcp) && app.sl.Hcp.length === 9;
  const q = slApplyHomography(app.sl.Hcp, 24, 18);
  out.calibMaps = Math.hypot(q.x - 50, q.y - 50) < 1;

  // Build a mask layer with the right shape.
  const pts = [{x:10,y:10},{x:90,y:10},{x:90,y:90},{x:10,y:90}];
  const L = slBuildMaskLayer(pts);
  out.layerShape = L.type === 'mask' && L.enabled === true && !!L.id && !!L.name
    && L.points.length === 4 && typeof L.hardness === 'number';

  // Commit: layers grow by one, it's selected, undo removes it.
  const n0 = app.layers.length;
  const committed = slCommitMask(pts);
  out.committed = app.layers.length === n0 + 1
    && app.layers[app.layers.length - 1].id === committed.id
    && app.selectedLayerId === committed.id;
  undo();
  out.undoRemoved = app.layers.length === n0 && !app.layers.some(l => l.id === committed.id);

  // Too few points -> no layer.
  out.rejectsFew = slCommitMask([{x:1,y:1},{x:2,y:2}]) === null && app.layers.length === n0;

  // H_cp survives a save/load round-trip.
  slSetCalibration(camPts, projPts);
  const snap = await buildProjectSnapshot(false);
  app.sl.Hcp = null; app.sl.calib = null;
  await restoreFromSnapshot(snap, 'test');
  await new Promise(r => setTimeout(r, 200));
  const q2 = app.sl.Hcp ? slApplyHomography(app.sl.Hcp, 24, 18) : {x:0,y:0};
  out.hcpRestored = Array.isArray(app.sl.Hcp) && app.sl.Hcp.length === 9 && Math.hypot(q2.x - 50, q2.y - 50) < 1;
  return out;
}
"""


# Camera I/O: full-res frame grab + the render-loop pattern flash used for capture.
JS_CAMERA = """
async () => {
  const out = {};
  await startWebcam();
  await new Promise(r => setTimeout(r, 600));
  const cam = app.mediaLibrary.find(m => m.kind === 'camera' && m.element && m.element.videoWidth > 0);
  out.haveCam = !!cam;

  const f = slGrabCameraFrame(cam);
  out.grabDims = !!f && f.width > 0 && f.height > 0 && f.data.length === f.width * f.height * 4;
  out.grabHasPixels = !!f && f.data.some(v => v !== 0);

  // Flash override: project a solid frame; the centre pixel takes the flash colour.
  const w = app.canvas.logicalWidth, h = app.canvas.logicalHeight;
  const cx = (w / 2) | 0, cy = (h / 2) | 0;
  app.sl.flash = '#ff0000'; renderProjection(0);
  const px = app.canvas.ctx.getImageData(cx, cy, 1, 1).data;
  out.flashRed = px[0] > 200 && px[1] < 60 && px[2] < 60;
  app.sl.flash = null; renderProjection(0);
  const px2 = app.canvas.ctx.getImageData(cx, cy, 1, 1).data;
  out.flashCleared = !(px2[0] > 200 && px2[1] < 60 && px2[2] < 60);
  return out;
}
"""


# Map orchestration: guards + capture flow (detection itself needs real hardware).
JS_MAP = """
async () => {
  const out = {};
  await startWebcam();
  await new Promise(r => setTimeout(r, 400));

  // No calibration -> refuses with a clear reason, adds no layer.
  app.sl.Hcp = null; app.sl.calib = null;
  const n0 = app.layers.length;
  const r1 = await slMap({ driftCheck: false, settleFrames: 2 });
  out.needsCalib = !!r1 && r1.ok === false && r1.reason === 'no-calibration';
  out.guardNoLayer = app.layers.length === n0;

  // With calibration but (headless) no projection reaching the camera, black and
  // white grabs match -> nothing detected -> structured result, no throw, no stray layer.
  slSetCalibration([{x:0,y:0},{x:48,y:0},{x:48,y:36},{x:0,y:36}],
                   [{x:0,y:0},{x:100,y:0},{x:100,y:100},{x:0,y:100}]);
  const n1 = app.layers.length;
  const r2 = await slMap({ driftCheck: false, settleFrames: 2 });
  out.ranOk = !!r2 && typeof r2.ok === 'boolean';
  out.layerInvariant = r2.ok === true ? app.layers.length === n1 + 1 : app.layers.length === n1;
  app.sl.flash = null;
  return out;
}
"""


# UI wiring: buttons exist, underlay toggles, calibration overlay + math round-trip.
JS_UI = """
async () => {
  const out = {};
  await startWebcam();
  await new Promise(r => setTimeout(r, 400));
  out.buttons = !!document.getElementById('slMapBtn')
    && !!document.getElementById('slCalibrateBtn')
    && !!document.getElementById('slUnderlayBtn');

  // Underlay toggle flips the flag both ways.
  app.sl.underlay = false;
  document.getElementById('slUnderlayBtn').click();
  out.underlayOn = app.sl.underlay === true;
  document.getElementById('slUnderlayBtn').click();
  out.underlayOff = app.sl.underlay === false;

  // Calibrate opens an overlay and projects the white quad.
  slStartCalibrate();
  out.calibOpen = !!document.getElementById('slCalibrateOverlay')
    && app.sl.flash === '#fff' && app.sl.calibrating === true;

  // Finishing with the 4 camera-frame corners calibrates, then cleans up.
  const cam = slLiveCamera();
  const vw = cam.element.videoWidth, vh = cam.element.videoHeight;
  const ok = slFinishCalibrate([{x:0,y:0},{x:vw,y:0},{x:vw,y:vh},{x:0,y:vh}]);
  slCancelCalibrate();
  out.calibFinish = ok === true && Array.isArray(app.sl.Hcp);
  out.calibClosed = !document.getElementById('slCalibrateOverlay')
    && app.sl.flash === null && app.sl.calibrating === false;

  const q = slApplyHomography(app.sl.Hcp, vw / 2, vh / 2);
  out.calibMapsCentre = Math.hypot(q.x - 50, q.y - 50) < 2;
  return out;
}
"""


def main():
    httpd = serve()
    url = f"http://127.0.0.1:{PORT}/index.html"
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=[
            "--no-sandbox", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_timeout(600)

        try:
            h = page.evaluate(JS_HOMOGRAPHY)
        except Exception as e:  # functions missing -> ReferenceError. That IS the red failure.
            h = {"solved": False, "error": str(e).splitlines()[0]}
        check("homography: solve, apply, invert, recover true map, reject degenerate",
              all(h.get(k) for k in ["solved", "cornersOk", "interiorOk", "invertOk", "degenerateNull"]),
              json.dumps(h))

        try:
            pl = page.evaluate(JS_PIPELINE)
        except Exception as e:
            pl = {"error": str(e).splitlines()[0]}
        check("diff-mask pipeline: diff, Otsu, morphology, contour, simplify",
              all(pl.get(k) for k in ["diffLen", "diffObject", "diffBg", "otsu", "binObj",
                                      "speckleGone", "holeFilled", "blobKept", "contourClosed",
                                      "contourBounds", "simpFew", "simpBounds"]),
              json.dumps(pl))

        try:
            dt = page.evaluate(JS_DETECT)
        except Exception as e:
            dt = {"error": str(e).splitlines()[0]}
        check("detector -> silhouette polygon in canvas-% via H_cp, empty scene -> null",
              all(dt.get(k) for k in ["got", "inRange", "boundsX", "boundsY", "emptyNull"]),
              json.dumps(dt))

        try:
            gl = page.evaluate(JS_GLUE)
        except Exception as e:
            gl = {"error": str(e).splitlines()[0]}
        check("glue: store calibration, build + commit mask, undo, reject, save/load H_cp",
              all(gl.get(k) for k in ["calibSet", "hcpStored", "calibMaps", "layerShape",
                                      "committed", "undoRemoved", "rejectsFew", "hcpRestored"]),
              json.dumps(gl))

        try:
            cam = page.evaluate(JS_CAMERA)
        except Exception as e:
            cam = {"error": str(e).splitlines()[0]}
        check("camera: full-res grab + render-loop pattern flash",
              all(cam.get(k) for k in ["haveCam", "grabDims", "grabHasPixels", "flashRed", "flashCleared"]),
              json.dumps(cam))

        try:
            mp = page.evaluate(JS_MAP)
        except Exception as e:
            mp = {"error": str(e).splitlines()[0]}
        check("map: refuses without calibration, runs capture flow without throwing",
              all(mp.get(k) for k in ["needsCalib", "guardNoLayer", "ranOk", "layerInvariant"]),
              json.dumps(mp))

        try:
            ui = page.evaluate(JS_UI)
        except Exception as e:
            ui = {"error": str(e).splitlines()[0]}
        check("ui: buttons, underlay toggle, calibration overlay + math round-trip",
              all(ui.get(k) for k in ["buttons", "underlayOn", "underlayOff", "calibOpen",
                                      "calibFinish", "calibClosed", "calibMapsCentre"]),
              json.dumps(ui))

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
