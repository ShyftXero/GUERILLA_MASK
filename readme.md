# GUERILLA_MASK

A single-file projection-mapping tool for demonstrations and pop-up actions. Offline, in a browser, on a modest laptop with a common projector. Map images, GIFs, videos, webcam, or generated patterns onto surfaces, cut holes with masks, bounce objects around the holes, switch looks with a MIDI pad. Save and load a project as one self-contained JSON.

![GUERILLA_MASK: library, scenes, layers with physics objects, inspector](demos/ui.gif)

## Why GUERILLA_MASK

- One HTML file. Open it locally, no install. Offline after first open if cached.
- Cheap or old projectors and laptops.
- Few controls, predictable under pressure, learnable in minutes.

Try it -> https://shyftxero.github.io/GUERILLA_MASK/

## Core features

- Three layer types. Projection: warp a media item to a 4-point quad. Mask: polygon that blocks areas of the output. Physics: bouncing objects (shapes or any media) that collide with arena edges, every mask, and each other.
- Media: images, GIFs (via gifler), videos
- Built-in patterns (no files needed): Plasma, Perlin Noise, Lasers, Hexagons, Triangles, Circles, Rectangles, Stripes. Each has speed/scale/hue sliders and maps onto a quad like any other media.
- GPU effects (WebGL) with any library item as source: Feedback / Kaleidoscope (recursive zoom, warp, rotate, N-axis mirror, hue drift, edge glow), Kaleidoscope (mirror only), Reaction-Diffusion (Gray-Scott, seeded by source silhouette), Motion Cut (pixels that stop changing learn into a background and go black, like a video-call background filter)
- Webcam as media: on a quad, into an effect, or bouncing in a physics arena. URL media: a YouTube link (embedded player warped with the same corner handles) or a direct mp4/webm URL (same as a local video). MJPEG streams from a phone, laptop, Pi, or IP cam on the hotspot: paste the URL, it reconnects by itself. Senders and scripts in `streaming.md`.
- Every destructive action (delete layer/object/scene/media, clear objects, clear MIDI, discard autosave, replace project on load) goes through one confirm dialog. Enter confirms, Esc cancels.
- Signals: microphone (bass / mid / high / level / beat) and webcam motion. Any pattern or physics parameter can react to one. Beats can randomize hue or kick physics objects.
- Scenes: snapshot a look, recall with keys 1–9 or MIDI
- Hardness, like a Photoshop brush: 100 = crisp edge, lower feathers the rim of a quad, mask, or physics object. Per layer and per object. Quads warp the fade border with the quad, so it follows the perspective.
- Stage edge fade: a black fade border over the whole output (rectangle or oval) to hide a projector's frame or blend two projectors. Inspector, Stage section, saved with the project.
- Real-world scale: tell the app how wide the projected image is at the wall (type it, or 📏 Measure a door) and every layer reports its size in feet/inches, cm, or meters. Type `8'` into Height and the quad becomes eight feet tall. Arrow keys nudge by inches. A yellow ruler stays on the measured landmark; after a bump, drag its ends back and the scene realigns.
- Layer reordering, selection, delete with undo. Blackout key (B), webcam kill key (C), Toggle Handles, Fullscreen with screen wake lock. HUD and buttons hide in fullscreen.
- Save/Load as one JSON with every image, GIF, and video embedded. Autosave to IndexedDB (no 5 MB cap) with original media cached, so a crash or reload comes back complete.

## Quick start (field workflow)

1. Open `index.html` in Chrome or Edge (Firefox works minus Web MIDI). From disk (`file://`) everything works except YouTube embeds. For YouTube run `./serve.sh` (`serve.cmd` on Windows) and open http://localhost:8000/. Plain `http://` over LAN blocks webcam, mic, and MIDI.
2. Drop media onto the library (PNG/JPG, GIF, MP4) or press 📷 Cam.
3. Press + Projection in the top bar, then click 4 points clockwise on the surface in the live view.
4. Click a library thumbnail to put it on the selected layer, or drag it onto the stage: it lands as a third-width quad under the pointer. Drag into a selected physics arena for a bouncing sprite. OS files dropped on the stage load and place in one go. Alt+click only inspects.
5. Press + Mask to hide spill on windows, signs, people. Click 3+ points, then Done (or Enter).
6. Press + in the scene strip to snapshot the look. Repeat per look.
7. Press F for fullscreen. Handles hide. B blacks out, B again restores. P overlays the panels over the live output without resizing the stage; add layers, drag thumbnails, tweak sliders, P again to hide.

Layout: top bar (project, new layers, signal meters, inputs), left panel (library thumbnails, scene pads, layer list), stage, right inspector (selected scene, layer, and media). Drag layer rows to reorder. I hides the inspector.

No artwork? Pick a pattern from the dropdown under the library and press + Pattern. It lands in the library and assigns to the selected empty Projection layer. ⚙ on a pattern sets speed, scale, and hue.

## Demos

Ready-made projects in `demos/`. Press 📂 Load, pick one, press F. No media files needed, every demo is built from patterns. Keys 1-9 switch scenes. Turn on 🎤 Mic and they react to the room.

### Kitchen Sink: `demos/kitchen-sink.json`

![Kitchen Sink](demos/kitchen-sink.gif)

Everything in one file. Scene 1: a grid with one quad per source, all eight patterns, a kaleidoscope fed by plasma, a YouTube embed, a remote mp4, the webcam. Scene 2: Motion Cut into alien skin and a feedback tunnel with a masked doorway. Scene 3: a row of camera filters (raw, neon edges, posterize, pixelated mp4) over Motion Cut. Scene 4: shapes, a reaction-diffusion sprite, a half-transparent video and a hidden object bouncing over a warped YouTube backdrop with a masked window. Scene 5: the mandala wall. Scenes are bound to MIDI notes 36-40, four knobs mapped (CC1 plasma speed, CC2 tunnel zoom, CC3 skin wiggle, CC7 gravity), program change on.

### Wall Mandala: `demos/wall-mandala.json`

![Wall Mandala](demos/wall-mandala.gif)

Triptych for a wide wall: hexagon wing, kaleidoscope-of-plasma center, laser wing, mask keeping the doorway dark. Bass changes the mandala's symmetry, highs scale the lasers, beats recolor them. Scenes: Triptych, Coral (reaction-diffusion center), Full mandala.

### Window Dodge: `demos/window-dodge.json`

![Window Dodge](demos/window-dodge.gif)

Full-canvas physics arena with two masked windows and a masked sign. Shapes, a reaction-diffusion sprite, and a plasma ball bounce around them, never into them. Grab any and throw it. Trails on, bass swells object size, beats kick everything, Space bumps the pile. Scenes: Bounce, Zero-G pinball (stripes backdrop), Heavy rain.

### Mirror Tunnel: `demos/mirror-tunnel.json`

![Mirror Tunnel](demos/mirror-tunnel.gif)

Needs a webcam (asks on load). Everything runs through Motion Cut: the wall and parked cars behind you fade to black, only moving people reach the projector. Scenes: Alien skin (reaction-diffusion grows out of your silhouette), Tunnel (six-fold feedback, motion drives zoom, beats recolor), Neon ghost (tinted Motion Cut, you appear only while moving), Mandala, Split. The GIF above was recorded with a synthetic test camera that never stops moving, so the whole frame is lit; a real camera shows only the person.

Rebuild with `tests/make_demos.py` (JSON + stills) and `tests/make_gifs.py` (GIFs). Both drive headless Chrome, so the files match the current save format.

## Webcam, effects, and audio reactivity

- **Webcam**: press 📷 Webcam. It appears in the library like a file. Click it to put it on the selected Projection or Physics layer.
- **Effects on media**: select a layer (or physics object) and use the "+ Effect" dropdown in the inspector, or drag an effect thumbnail onto a layer row. The effect wraps whatever the layer shows: GIF, PNG, video, webcam, pattern, or another effect. Each wrap is its own instance, so two Corals on two layers can differ. The inspector shows the chain (`flower.gif → Reaction → Kaleido`); click a link to edit that stage, "Remove top effect" unwraps one. YouTube cannot be wrapped (browsers block reading its pixels).
- **Effects** (✨ in the pattern dropdown): Feedback / Kaleidoscope, Kaleidoscope, Reaction-Diffusion, Motion Cut, Filter. Adding one from the dropdown uses the selected layer's media as source, then the webcam, then the newest file. "(no source)" on a thumbnail means it shows only its built-in seed; set Source in the inspector.
  - Filter: one cheap pass with a Mode switch: edges, neon edges (colored by edge direction), posterize, threshold, pixelate, invert, solarize, false color, mirror. Amount tunes the mode. Point it at the webcam for live looks.
  - Feedback: Feedback toward 0.99 for long trails, Zoom above 1 for a tunnel, below 1 for an implosion. Symmetry folds the image into a mandala. Edges makes the webcam a neon outline so only movement smears into the loop.
  - Reaction-Diffusion: Feed/Kill pick the organism (0.037/0.06 = worms, 0.055/0.062 = coral, 0.03/0.057 = spots). Src seed injects the source silhouette as chemical B. Wiggle / Wiggle freq warp the pattern through a rolling sine field. Rim glow lights the edges. Reset re-seeds.
  - Motion Cut: point it at the webcam, then chain other effects off it (set their Source to the Motion Cut) so only moving people drive them. Fade time = how fast a still thing vanishes. Sensitivity = how much change counts. Hold = how long a pause is forgiven. Ghost bg leaves a faint trace of the background. Tint colors the foreground. Relearn resets the background after the camera moves.
- **Quality** (top bar: Low / Med / High): camera capture size (360p / 720p / 1080p, changed live, no re-prompt) and the buffer size of every pattern and effect (×0.5 / ×1 / ×1.5, resized in place). Drop to Low when webcam effects stutter on an old laptop. Saved with the project.
- **Mic**: press 🎤 Mic. Meters show bass, mid, high, level, beat. Webcam motion shows once a webcam is live.
- **React**: in any pattern's ⚙ panel, or in the Physics Arena panel, set React = signal, choose a parameter, and an Amount (negative inverts). Example: bass → Zoom on Feedback, motion → Speed on Hexagons, beat → Size on physics.
- **On beat**: patterns can randomize hue; physics layers can kick every object with a random impulse.

Mic and webcam need a user click to start (browser permission). Saved projects remember them and re-request on load.

## Streams from other people

Others on the hotspot run a sender (phone app, VLC, ustreamer, ffmpeg); you paste `http://<their-ip>:8080/video` into `+ URL`. See `streaming.md` for senders, scripts in `stream/`, and why effects need a CORS header.

## Scale, size, and realign (inches on the wall)

Percent coordinates survive resolution changes, but on site you think in feet: "the banner has to be 8 ft tall and start 3 ft above the door". The 📏 Scale section at the top of the inspector turns stage percent into real units.

1. Go fullscreen on the projector (F, then P for the panels) so the stage has the projector's aspect.
2. Press 📏 Measure, click both sides of something you know the size of (a door is ~6'8" tall, 3' wide; a brick course is 2⅝"), type the distance (`6'8"`, `80in`, `2.03m`), Enter. The app computes the width of the projected image and shows `1 in = N px`.
   - Or type the image width into Wall width if you know the throw.
3. Select any layer. Under its settings: `on the wall 12'5" × 8'0"`, editable Width / Height (keep proportions on by default), Center X / Y from the top-left of the image, and a nudge pad. Type `8'` into Height: the quad scales about its center to eight feet. If that pushes it off the stage it slides back inside instead of clipping.
4. Arrow keys move the selected layer (or physics object) by the Nudge step, Shift for ×10. Default step is 1 inch.
5. Physics objects get a Diameter field in the same units.

**Realign after a bump.** The measured ruler stays on the stage as a yellow dashed line with two draggable ends. When someone kicks the tripod, drag the ends back onto their landmark and the scale updates. Tick *Realign: ruler drags the whole scene* first and every layer, mask, and physics object follows the ruler (move, scale, rotate). Units (ft/in, inches, cm, m), the ruler, and the nudge step are saved with the project and the autosave.

Caveat: height is derived from width via the output's aspect, so a keystoned projector lies a little vertically. Measure a vertical landmark if the vertical dimension matters more.

## Scenes and MIDI

**Scenes** snapshot the layer stack plus every pattern's settings. The media library is shared across scenes.

1. Build a look, press + Scene. Repeat per look.
2. Click a scene pad to recall it. Keys 1–9 recall by number. Double-click to rename.
3. The active scene is live: changes write back when you switch away or save. 💾 in the inspector forces a write.
4. 📑 duplicates a scene. Map the room once (quads, masks, arena), duplicate, swap the media on the copy. The copy lands after the original, becomes active, and has no MIDI note.

**MIDI** (Chrome/Edge, Web MIDI):

- Press 🎹 MIDI once. Devices hot-plug.
- Scenes: press 🎹 on a scene, then hit a pad or key. Program change also recalls scenes by index (PC 0 = scene 1).
- Knobs: every slider in the inspector (pattern params, physics arena) has a 🎛 learn button. Click it, move a knob or fader. The button turns green and shows the CC number; × beside it clears. Esc cancels a learn.
- The MIDI section at the bottom of the inspector lists every binding (notes to scenes, CCs to sliders) with × per row and Clear all. Bindings and CC maps save in the project JSON and the autosave.

## Physics layer (bouncing objects)

1. Choose Physics, press + Add Layer.
2. Optional: click 3+ points to draw an arena polygon, then Complete Shape. No points = whole canvas.
3. Physics Arena panel adds circles, rects, triangles, hexagons. Click any library item (GIF, video, image, pattern) to add it as a bouncing sprite.
4. Sliders: Gravity, Speed, Bounce (restitution), Size, Spin, Trails, Hardness (every object). Shuffle re-rolls positions.
5. A physics layer is a group: objects are indented rows under it in the layer list. Click a row to select the object (inspector shows kind, shape, color, media, size, opacity, hardness, spin, effect chain), drag rows to change draw order, 🗑 or Delete removes it. With handles on, every object gets a green outline; the selected one also gets a scale square and a rotate handle.
6. Grab any object with mouse or finger and throw it. Works with handles hidden and in fullscreen. The Bump hotkey (default Space, change it in the physics panel) shakes every object in every physics layer, biased upward so settled piles lift.

Objects never enter Mask polygons: masks are solid walls, so blocked-out windows, signs, and people stay clear. ⬠ on the layer row redraws the arena.

Tip: prepare several saved JSONs (different surfaces/messages) and load them on site.

## Roadmap

See `ROADMAP.md` and the GitHub issues. Headline: coordination across several laptops and projectors (#2): state sync, synced scene switches, webcam-measured projector offsets, auto-alignment.

## Minimal hardware

Any laptop from the last decade with a modern browser. A common 720p/1080p projector (short-throw helps, not required). Optional tripod or clamp mount. Extension cord and gaffer tape. No special GPU or drivers.

## Controls and shortcuts

- B: Blackout output (panic key). B again restores.
- C: Kill the webcam stream (privacy). Click 📷 Webcam to restart.
- F: Fullscreen (whole page; panels hide, handles hide, screen wake lock on)
- P: In fullscreen, overlay the panels on the stage without resizing it. P again hides them.
- H: Toggle handles
- I: Toggle the inspector panel
- Enter: Finish placing points (same as Done)
- 1–9: Recall scene by number
- Delete: Delete active layer or object.
- Ctrl+Z / Ctrl+Shift+Z (Cmd on Mac): undo / redo any layer edit: move, scale, rotate, point, reorder, delete, add, nudge, ruler realign. 10 deep. Cleared on load and scene recall.
- Arrow keys: Nudge the selected layer or physics object by the Scale nudge step (Shift ×10). Without calibration, 0.5% of the stage.
- Space: Bump all physics objects (configurable in the physics panel)
- Esc: Cancel point placement or a MIDI learn
- Mouse or touch (pointer events, tablets work). Projection: click 4 points clockwise. Mask / Physics arena: click 3+ points, then Complete Shape. Selected layer: drag the outline or center handle to move, the green square to scale, the purple circle to rotate.

## Save/Load and autosave

- **Save** writes one JSON with everything embedded: images, GIFs, videos (base64), patterns (parameters), scenes, MIDI maps. Big videos make big files; the HUD reports the size. Copy it to a USB stick and it loads anywhere with nothing to relink.
- **Load** restores the file. If a media item is missing (older file without embedded data) a relink prompt lists only the missing ones. Or cancel and drop the file into the library later; it relinks by filename.
- **Autosave** runs 600 ms after any change into IndexedDB, with the original media blobs cached alongside. Nothing is re-encoded, so it costs nothing mid-show. Next open offers the recovery. If autosave fails the HUD says so in capitals; save a file.
- Sample projects in `gifs/`. Old versions and the original spec in `archive/`.

## Field checklist

- Build the offline file before you go: `./build.sh` writes `dist/index.html` with gifler inlined — one self-contained file, no CDN, GIFs animate with zero network. Copy that to the show laptop or a USB stick. The dev `index.html` fetches gifler from a CDN on first open (GIFs fall back to a still frame if it can't), so don't rely on it where there's no signal.
- Charge laptop; disable auto-updates. Fullscreen requests a wake lock, but set the OS to never sleep anyway.
- Open the page from disk or https. On a LAN `http://` address the webcam, mic, and MIDI buttons cannot start.
- Browser zoom 100%. Press B once to confirm blackout works. Test fullscreen and handle toggle before moving.
- Pre-focus and keystone the projector. Spare HDMI/USB-C adapters, long power cable, tape.
- Dark, contrasty artwork; legible fonts.

## Tips for alignment on uneven surfaces

- Put the four Projection points on strong corners (windows, tiles, bricks). Keep point order clockwise to avoid twisted quads.
- Mask layers clip spill around edges, signs, foliage.
- For wide walls, split into several Projection layers with different media.

## Safety and operational considerations

Don't shine into windows or traffic. Keep cables tidy. Have spotters and plan a quick pack-up. Know local guidelines and laws before operating.

## Troubleshooting

- Nothing shows on a Projection layer: check 4 points, media assigned, media finished loading, and B not engaged (the Black button turns red).
- GIF/Video missing after loading a JSON: older files did not embed them. Drop the original file into the library; it relinks by filename.
- A pattern or effect went black mid-show: WebGL context lost (projector hotplug, GPU reset). It rebuilds when the context returns; the HUD reports both events.
- Stream stays on "connecting…": open the URL in a browser tab first. If the tab plays it, the app will. If the page is https, http streams are blocked: open from disk or `./serve.sh`.
- YouTube quad shows "error 153" / "Video player configuration error": YouTube refuses embeds with no referrer, and a page opened from disk sends none. Run `./serve.sh`, then open http://localhost:8000/. Also fails behind referrer-stripping extensions or privacy settings.
- Webcam / mic / MIDI button says it needs https: you opened the page over plain http on a LAN. Use the file from disk or an https host.
- Physics says object cap reached: 40 per layer keeps old laptops smooth. Remove some or add another physics layer.
- Output looks soft: check browser zoom and devicePixelRatio; try 100% zoom.
- Seams in warped media: adjust points slightly; the renderer expands triangles to reduce gaps.

## Technical notes

- Single HTML file (vanilla JS + inline CSS). A section index comment sits at the top of the script. Tunable constants live in one `TUNING` object.
- GIF decoding via gifler. Dev `index.html` loads it from a CDN; `./build.sh` (`tools/build_offline.py`) inlines the vendored copy (`vendor/gifler.min.js`) into `dist/index.html` as its own `<script>` appended before `</body>` — never spliced into the app script — for a no-network single file. `tests/test_offline_build.py` verifies the built file runs with all external network blocked. If the decoder is missing (un-built copy opened offline) GIFs fall back to still frames with a HUD warning. Zero-delay GIF frames are clamped to 100 ms, same as browsers, because gifler otherwise spins forever.
- Persistence: IndexedDB stores `kv/autosave` (snapshot, no media data) and `files/<kind>:<name>` (original blobs). Save embeds blobs as data URLs.
- Tests: `./tests/run.sh` drives headless Chrome through load, physics, scenes, MIDI, autosave, and a fresh-machine Save/Load round trip. Needs `uv` and a Chrome binary. Large sample media is marked for Git LFS in `.gitattributes`.
- Patterns render into offscreen canvases (pixel generators at 128–160px, vector ones at 512px) and only tick when a layer uses them. Effects run in their own WebGL context with ping-pong framebuffers (feedback at 512px, reaction-diffusion at 256px with half-float state when available, 8 sim steps per frame).
- Audio: AnalyserNode (fft 1024), band averages with attack/release smoothing, beat = bass spike above running average with a 220 ms refractory period. Motion: frame difference of the webcam downsampled to 48×36.
- Physics: circle colliders, polygon edge collision against arena + masks, pairwise elastic collisions, 2 sub-steps per frame
- Canvas with devicePixelRatio scaling. Projection renders via grid subdivision into triangles. Percent coordinates (0–100) so layouts survive resolution changes.
- Real-world scale stores one number, the projected image width in inches (`settings.scale.wallWidthIn`); height follows the output aspect (stage in fullscreen, otherwise the screen). Lengths parse from `8' 6"`, `102in`, `2.6m`, `260cm` and format in the chosen units. The ruler is two stage-percent points plus its real length; dragging an end re-derives the width, and with Realign on applies a similarity transform (translate, uniform scale, rotate) to every layer polygon and physics object.
