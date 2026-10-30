# GUERILLA_MASK

Single-file projection mapper. Open in a browser, offline, on any laptop with a projector.

Map images, GIFs, videos, webcam, or built-in patterns onto surfaces. Cut holes with masks. Bounce objects around the holes. React to the room. Switch looks with a MIDI pad.

Try it → https://shyftxero.github.io/GUERILLA_MASK/

![GUERILLA_MASK: library, scenes, layers with physics objects, inspector](demos/ui.gif)

## Why

- One HTML file. No install. Works offline.
- Runs on old hardware — any laptop from the last decade plus a common projector.
- Few controls, predictable under pressure.

## Layer types

- **Projection** — warp a media item to a 4-point quad on the surface.
- **Mask** — polygon that blocks areas of the output. Masks are solid walls: physics objects never enter them.
- **Physics** — bouncing objects (shapes or any media) that collide with edges, masks, and each other.

Each layer has a **Hardness** slider: 100 = crisp edge, lower feathers the rim (follows the quad's perspective on Projection layers). Per-object too. **Stage edge fade** (Stage section of the inspector) adds a black border — rectangle or oval — over the whole output, to hide a projector's frame or blend two projectors.

## Media

- Files: images, GIFs (gifler), video (mp4/webm).
- Live: webcam (📷), MJPEG streams (paste `http://<ip>:8080/video` — reconnects on its own), YouTube, direct mp4/webm URLs.
- Built-in patterns (no files needed): Plasma, Perlin Noise, Lasers, Hexagons, Triangles, Circles, Rectangles, Stripes. Speed/scale/hue sliders on each.
- WebGL effects: Feedback/Kaleidoscope, Kaleidoscope, Reaction-Diffusion, Motion Cut, Filter. Stack them per layer.

## Signals

🎤 Mic gives you bass / mid / high / level / beat. Webcam motion is a signal once a camera is live. Any pattern or physics parameter can react to one. Beats can randomize hue or kick physics objects.

Mic and webcam need a user click to start (browser permission). Saved projects re-request on load.

## Quick start

1. Open `index.html` in Chrome or Edge. Firefox works minus Web MIDI. From disk (`file://`) everything runs except YouTube embeds — for those, run `./serve.sh` (`serve.cmd` on Windows) and open `http://localhost:8000/`. Plain `http://` over LAN blocks webcam, mic, and MIDI.
2. Drop media onto the library (PNG/JPG, GIF, MP4) or press 📷 Cam.
3. **+ Projection** in the top bar → click 4 points clockwise on the surface.
4. Click a thumbnail to put it on the selected layer. Or drag onto the stage (lands as a third-width quad). Drag into a physics layer for a bouncing sprite. OS files dropped onto the stage load and place in one go.
5. **+ Mask** to block spill on windows, signs, people. Click 3+ points, then Done (or Enter).
6. **+** in the scene strip to snapshot the look. Repeat per look. Keys 1–9 recall scenes.
7. **F** for fullscreen. Handles hide. **B** blacks out, **B** restores. **P** overlays the panels on the stage without resizing it.

No artwork? Pick a pattern from the dropdown under the library and press **+ Pattern**.

Layout: top bar (project, new layers, signal meters, inputs), left panel (library, scene pads, layer list), stage, right inspector (selected scene, layer, and media). Drag layer rows to reorder. **I** hides the inspector.

## Structured-light mapping (experimental)

Calibrate once, then auto-cut masks around real objects using the webcam.

1. **🎯 Calibrate** — project a white quad, click its 4 corners in the webcam view. Aligns camera to projector so the tool knows where it's pointing.
2. **👁 Underlay** — webcam under your layers so you can see the surface while mapping on-screen.
3. **🗺 Map** — flash black/white, read which pixels lit up, auto-cut a mask around the object. Works on near-planar surfaces (doorframes, columns, walls). v1.
4. **🔺 Faces** (pro mode) — map a 3D object's visible faces individually, like a pyramid. Calibrate first.

## Demos

Ready-made projects in `demos/`. Press 📂 Load, pick one, press F. No media files needed — all built-in patterns. Keys 1–9 switch scenes. Turn on 🎤 Mic and they react to the room.

### Kitchen Sink: `demos/kitchen-sink.json`

![Kitchen Sink](demos/kitchen-sink.gif)

Everything at once. Scene 1: all eight patterns, kaleidoscope on plasma, YouTube embed, remote mp4, webcam. Scene 2: Motion Cut into alien skin + feedback tunnel with a masked doorway. Scene 3: camera filters over Motion Cut. Scene 4: physics with reaction-diffusion sprite and warped YouTube behind masked windows. Scene 5: mandala wall. MIDI: notes 36–40 for scenes, CC1 plasma speed, CC2 tunnel zoom, CC3 skin wiggle, CC7 gravity, program change on.

### Wall Mandala: `demos/wall-mandala.json`

![Wall Mandala](demos/wall-mandala.gif)

Triptych for a wide wall: hex wing, kaleidoscope-of-plasma center, laser wing, masked doorway. Bass changes the mandala's symmetry, highs scale the lasers, beats recolor them. Scenes: Triptych, Coral (reaction-diffusion center), Full mandala.

### Window Dodge: `demos/window-dodge.json`

![Window Dodge](demos/window-dodge.gif)

Full-canvas physics arena with two masked windows and a masked sign. Shapes, a reaction-diffusion sprite, and a plasma ball bounce around them — never into them. Grab and throw. Trails on, bass swells size, beats kick everything, Space bumps the pile. Scenes: Bounce, Zero-G pinball (stripes backdrop), Heavy rain.

### Mirror Tunnel: `demos/mirror-tunnel.json`

![Mirror Tunnel](demos/mirror-tunnel.gif)

Needs a webcam. Motion Cut strips the static scene — only moving people reach the projector. Scenes: Alien skin (reaction-diffusion from your silhouette), Tunnel (six-fold feedback, motion drives zoom, beats recolor), Neon ghost, Mandala, Split. The GIF uses a synthetic camera that never stops moving; a real camera shows only the person.

Rebuild with `tests/make_demos.py` (JSON + stills) and `tests/make_gifs.py` (GIFs). Both drive headless Chrome.

## Effects

Select a layer, use **+ Effect** in the inspector, or drag an effect thumbnail onto a layer row. The inspector shows the chain (`flower.gif → Reaction → Kaleido`); click a link to edit that stage, Remove top effect unwraps one. YouTube can't be wrapped (browsers block reading its pixels).

- **Feedback/Kaleidoscope** — recursive zoom/warp/rotate/mirror. Zoom > 1 = tunnel, < 1 = implosion. Symmetry folds into a mandala. Edges mode turns webcam into neon outlines so only movement smears into the loop.
- **Kaleidoscope** — mirror only.
- **Reaction-Diffusion** — Gray-Scott sim. Feed/Kill pick the organism (0.037/0.06 = worms, 0.055/0.062 = coral, 0.03/0.057 = spots). Src seed injects the source silhouette as chemical B. Wiggle / Wiggle freq warp it through a rolling sine field. Rim glow lights the edges. Reset re-seeds.
- **Motion Cut** — pixels that stop changing learn into the background and go black. Point at webcam → chain other effects off it so only moving people drive them. Fade time, Sensitivity, Hold, Ghost bg, Tint. Relearn resets after the camera moves.
- **Filter** — cheap single pass: edges, neon edges (colored by direction), posterize, threshold, pixelate, invert, solarize, false color, mirror. Amount tunes the mode.

**Quality** (Low / Med / High in the top bar): camera capture size (360p / 720p / 1080p) and effect buffer size (×0.5 / ×1 / ×1.5). Drop to Low when webcam effects stutter on an old laptop.

## Streams from other people

Others on the hotspot run a sender (phone app, VLC, ustreamer, ffmpeg). Paste `http://<their-ip>:8080/video` into **+ URL**. See `streaming.md` for senders, scripts in `stream/`, and why effects need a CORS header.

## Real-world scale

In the 📏 Scale section of the inspector:

1. Press 📏 Measure → click both sides of a known landmark (a door is ~6'8" tall, 3' wide; a brick course is 2⅝") → type the distance (`6'8"`, `80in`, `2.03m`) → Enter. Or type the image width directly into Wall width if you know the throw.
2. Select any layer — it now shows `12'5" × 8'0"` and you can type `8'` into Height to set it to eight feet tall. Arrow keys nudge by the step (default 1 inch, Shift ×10).
3. Physics objects get a Diameter field in the same units.

**Realign after a bump.** The measured ruler stays as a yellow dashed line on the stage with two draggable ends. Kick the tripod → drag the ends back to the landmark → tick *Realign* → every layer, mask, and object follows (translate, scale, rotate).

Caveat: height derives from width via the output's aspect, so a keystoned projector lies a little vertically. Measure a vertical landmark if that dimension matters more.

## Scenes and MIDI

Scenes snapshot the layer stack and every pattern's settings. The media library is shared across scenes. The active scene is live — changes write back when you switch away or save.

1. Build a look → **+ Scene**. Repeat per look. Double-click to rename.
2. Click a pad or press 1–9 to recall. **📑** duplicates a scene.
3. **💾** in the inspector forces a write to the current scene.

**MIDI** (Chrome/Edge, Web MIDI):

- Press **🎹** once — devices hot-plug.
- **Scenes**: press 🎹 on a scene pad → hit a pad or key to bind. Program change also recalls by index (PC 0 = scene 1).
- **Knobs**: click **🎛** beside any slider → move a knob → bound. Green shows the CC number, × clears. Esc cancels a learn.
- All bindings list in the MIDI section of the inspector with × per row and Clear all. Save in the project JSON.

## Physics

1. **+ Physics** → optional: click 3+ points for an arena polygon, then Complete Shape. No points = whole canvas.
2. Physics Arena panel adds circles, rects, triangles, hexagons, or any library item as a bouncing sprite.
3. Sliders: Gravity, Speed, Bounce, Size, Spin, Trails, Hardness (applies to every object). Shuffle re-rolls positions.
4. Objects are rows indented under the layer. Drag to reorder, 🗑 or Delete removes one. Click a row to select (inspector shows kind, shape, color, media, size, opacity, hardness, spin, effect chain).
5. Grab any object with mouse or finger and throw it — works with handles hidden and in fullscreen. Space (configurable in the physics panel) bumps everything biased upward so settled piles lift.

Objects never enter Mask polygons. ⬠ on the layer row redraws the arena.

## Save and autosave

**Save** writes one JSON with everything embedded — images, GIFs, videos as base64, patterns, scenes, MIDI maps. Copy to a USB stick and it loads anywhere with nothing to relink. Big videos make big files; the HUD shows the size.

**Load**: if a media item is missing (older file without embedded data), a relink prompt lists only the missing ones. Cancel and drop the file into the library later — it relinks by filename.

**Autosave** runs 600 ms after any change into IndexedDB with original media cached alongside. Next open offers recovery. If autosave fails the HUD says so in caps; save a file.

Every destructive action (delete layer/object/scene/media, clear objects, clear MIDI, discard autosave, replace project on load) goes through one confirm dialog. Enter confirms, Esc cancels.

## Controls and shortcuts

| Key | Action |
|-----|--------|
| B | Blackout (panic key). B again restores. |
| C | Kill the webcam stream. Click 📷 Webcam to restart. |
| F | Fullscreen — panels and handles hide, wake lock on. |
| P | In fullscreen: overlay panels on the stage without resizing it. |
| H | Toggle handles |
| I | Toggle inspector |
| 1–9 | Recall scene by number |
| Delete | Delete the selected layer or object |
| Ctrl+Z / Ctrl+Shift+Z | Undo / redo (10 deep; Cmd on Mac). Cleared on load and scene recall. |
| Arrow keys | Nudge selected layer or object by nudge step (Shift ×10) |
| Space | Bump all physics objects |
| Esc | Cancel point placement or MIDI learn |
| Enter | Finish placing points (same as Done) |

Projection: click 4 points clockwise. Mask / Physics arena: click 3+ points → Complete Shape. Selected layer: drag the outline or center handle to move, green square to scale, purple circle to rotate.

## Field checklist

- **Build the offline file before you go.** `./build.sh` → `index.offline.html` with gifler inlined — one self-contained file, no CDN, GIFs animate without network. The dev `index.html` fetches gifler from a CDN on first open; don't rely on it where there's no signal.
- Charge the laptop. Disable auto-updates. Set OS to never sleep (fullscreen requests a wake lock, but OS power settings still win).
- Open from disk or https. On a LAN `http://` address: webcam, mic, and MIDI cannot start.
- Browser zoom at 100%. Press B to confirm blackout, then B to restore. Test fullscreen and handle toggle before moving.
- Pre-focus and keystone the projector. Spare HDMI/USB-C adapters, long power cable, gaffer tape.
- Dark, contrasty artwork. Legible fonts.

## Alignment tips

- Put Projection points on strong corners — windows, tiles, bricks. Click clockwise to avoid twisted quads.
- Mask layers clip spill around edges, signs, foliage.
- Wide walls: split into several Projection layers with different media.

## Safety

Don't shine into windows or traffic. Keep cables tidy. Have spotters and a quick pack-up plan. Know local guidelines before operating.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Nothing on a Projection layer | 4 points placed? Media assigned and loaded? B not engaged (button turns red)? |
| GIF or video missing after load | Older file without embedded media. Drop the original into the library — it relinks by filename. |
| Pattern or effect went black mid-show | WebGL context lost (projector hotplug, GPU reset). Rebuilds automatically; HUD reports both events. |
| Stream stuck on "connecting…" | Open the URL in a browser tab first. If it plays there, the app will get it. https page + http stream = blocked — open from disk or `./serve.sh`. |
| YouTube shows "error 153" | YouTube refuses embeds without a referrer, and disk-opened pages send none. Run `./serve.sh`, open `http://localhost:8000/`. Also fails behind referrer-stripping extensions. |
| Webcam / mic / MIDI needs https | Opened over plain `http://` on a LAN. Use disk or an https host. |
| "Object cap reached" | 40 objects per physics layer. Remove some or add another layer. |
| Output looks soft | Check browser zoom and devicePixelRatio. Try 100% zoom. |
| Seams in warped media | Adjust points slightly — the renderer expands triangles to reduce gaps. |

## Hardware

Any laptop from the last decade with a modern browser. A 720p or 1080p projector. Optional tripod or clamp mount. Extension cord and gaffer tape.

## Technical notes

- Single HTML file: vanilla JS + inline CSS. Tunable constants in one `TUNING` object; a section index sits at the top of the script.
- GIF decoding via gifler. Dev `index.html` loads it from CDN; `./build.sh` (`tools/build_offline.py`) inlines the vendored copy (`vendor/gifler.min.js`) into `index.offline.html` as its own `<script>` appended before `</body>` — not spliced into the app script — for a zero-network single file. `tests/test_offline_build.py` verifies the built file runs with all external network blocked. Zero-delay GIF frames clamped to 100 ms (same as browsers; gifler otherwise spins indefinitely).
- Persistence: IndexedDB stores `kv/autosave` (snapshot, no media) and `files/<kind>:<name>` (original blobs). Save embeds blobs as data URLs.
- Tests: `./tests/run.sh` drives headless Chrome through load, physics, scenes, MIDI, autosave, and a fresh-machine Save/Load round trip. Needs `uv` and a Chrome binary. Large media is Git LFS in `.gitattributes`.
- Patterns: offscreen canvases (pixel generators at 128–160px, vector at 512px), tick only when a layer uses them.
- Effects: WebGL context, ping-pong framebuffers (feedback at 512px, reaction-diffusion at 256px with half-float when available, 8 sim steps per frame).
- Audio: AnalyserNode (fft 1024), band averages with attack/release smoothing. Beat = bass spike above running average with 220 ms refractory.
- Motion: frame difference of webcam downsampled to 48×36.
- Physics: circle colliders, polygon edge collision against arena + masks, pairwise elastic collisions, 2 sub-steps per frame.
- Canvas with devicePixelRatio scaling. Projection via grid subdivision into triangles. Percent coordinates (0–100) so layouts survive resolution changes.
- Real-world scale: one number (`settings.scale.wallWidthIn`); height derived from output aspect. Lengths parse `8' 6"`, `102in`, `2.6m`, `260cm`. Ruler realign applies a similarity transform (translate, uniform scale, rotate) to every layer polygon and physics object.

## Roadmap

`ROADMAP.md` and the GitHub issues. Headline: coordination across laptops and projectors (#2) — state sync, synced scene switches, webcam-measured offsets, auto-alignment.
