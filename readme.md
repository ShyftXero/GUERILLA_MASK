# GUERILLA_MASK

A single-file, no‑frills projection‑mapping tool designed for rapid deployment during demonstrations and pop‑up actions. Works offline in a modern browser, on modest laptops, with common projectors. Map images/GIFs/videos/webcam/generated patterns onto surfaces, cut holes with masks, bounce objects around the holes, switch looks with a MIDI pad. Save/load projects as one self‑contained JSON.

![GUERILLA_MASK: library, scenes, layers with physics objects, inspector](demos/ui.gif)

---
 
## Why GUERILLA_MASK

- Keep it simple, dependable, and easy to train in minutes
  - Runs from one HTML file (open locally; no install)
  - Prioritize offline use, modest hardware, and quick setup
  - Offline by default (after first open if cached)
- Empower communities to project messages without complex tooling
  - Works with cheap/older projectors and laptops
  - Simple, predictable controls under pressure

Try it -> https://shyftxero.github.io/GUERILLA_MASK/
---

## Core features

- Three layer types:
  - Projection: warp a media item to a 4‑point quad
  - Mask: polygon that blocks areas of the output
  - Physics: bouncing objects (shapes or any media) that collide with arena edges, every mask, and each other
- Media: images, GIFs (via gifler), videos
- Built‑in procedural patterns (no files needed): Plasma, Perlin Noise, Lasers, Hexagons, Triangles, Circles, Rectangles, Stripes. Each has speed/scale/hue sliders and maps onto a quad like any other media.
- GPU effects (WebGL) that take any library item as a source: Feedback / Kaleidoscope (recursive zoom, warp, rotate, N‑axis mirror, hue drift, edge glow), Kaleidoscope (mirror only), Reaction‑Diffusion (Gray‑Scott, seeded by source silhouette), Motion Cut (background fade: pixels that stop changing learn into a background and go black, like a video‑call background filter)
- Webcam as a media source: use it on a quad, feed it into an effect, or bounce it around in a physics arena
- URL media: paste a YouTube link (plays as an embedded player warped over the canvas with the same corner handles) or a direct mp4/webm URL (behaves like a local video)
- Every destructive action (delete layer/object/scene/media, clear objects, clear MIDI, discard autosave, replace project on load) goes through one confirm dialog. Enter confirms, Esc cancels.
- Live signals for modulation: microphone (bass / mid / high / level / beat) and webcam motion. Any pattern or physics parameter can react to a signal. Beats can randomize hue or kick physics objects.
- Scenes: snapshot a whole look, recall with keys 1–9 or MIDI
- Hardness, like a Photoshop brush: 100 = crisp edge, lower feathers the rim so a projection quad, a mask, or a physics object fades into whatever is beneath it. Per layer and per object. Quads use a fade border warped with the quad, so it follows the perspective.
- Stage edge fade: an adjustable black fade-border over the whole output (rectangle or oval) to hide a projector's hard frame or blend two projectors. In the inspector's Stage section, saved with the project.
- Real-world scale: tell the app how wide the projected image is at the wall (type it, or 📏 Measure a door) and every layer reports its size in feet/inches, cm, or meters. Type `8'` into Height and the quad becomes eight feet tall. Nudge by inches with the arrow keys. A yellow ruler stays on the landmark you measured; after a bump, drag its ends back and the whole scene realigns.
- Layer reordering, selection, delete with undo
- Blackout key (B), webcam kill key (C), Toggle Handles, Fullscreen with screen wake lock
- Save/Load project as one JSON with every image, GIF, and video embedded
- Autosave to IndexedDB (no 5 MB cap) with original media cached, so a crash or reload comes back complete
- HUD and buttons auto‑hide in fullscreen to keep output clean

---

## Quick start (field workflow)

1. Open `index.html` in Chrome or Edge (Firefox works minus Web MIDI). From disk (`file://`) everything works except YouTube embeds. For YouTube run `./serve.sh` (`serve.cmd` on Windows) and open http://localhost:8000/. Plain `http://` over LAN blocks webcam, mic, and MIDI.
2. Drop media onto the library (PNG/JPG, GIF, MP4) or press 📷 Cam.
3. Press + Projection in the top bar, then click 4 points clockwise on the surface in the live view.
4. Click a library thumbnail to put it on the selected layer, or drag it onto the stage: it lands as a third‑width quad under the pointer, ready to warp. Drag into a selected physics arena to make it a bouncing sprite. OS files dropped on the stage load and place in one go. Alt+click only inspects.
5. Press + Mask to hide spill on windows, signs, people. Click 3+ points, then Done (or Enter).
6. Press + in the scene strip to snapshot the look. Build more looks, snapshot each.

Layout: top bar (project, new layers, signal meters, inputs), left panel (library thumbnails, scene pads, layer list), stage, right inspector (everything about the selected scene, layer, and media). Drag layer rows to reorder. I hides the inspector.
7. Press F for fullscreen. Handles hide automatically. B blacks out instantly, B again restores. Need to fine-tune on the wall? P overlays the panels over the live output (the stage does not resize, so nothing jumps); add layers, drag thumbnails, tweak sliders, P again to hide.

No artwork on hand? Pick a pattern from the dropdown under the library and press + Pattern. It lands in the library and auto‑assigns to the selected empty Projection layer. Click ⚙ on a pattern to tweak speed, scale, and hue.

---

## Demos

Three ready‑made projects in `demos/`. Press 📂 Load, pick one, press F. No media files needed, every demo is built from patterns. Keys 1‑9 switch scenes. Turn on 🎤 Mic and they react to the room.

### Kitchen Sink — `demos/kitchen-sink.json`

![Kitchen Sink](demos/kitchen-sink.gif)

Everything in one file. Scene 1 is a grid with one quad per source: all eight patterns, a kaleidoscope fed by plasma, a YouTube embed, a remote mp4, the webcam. Scene 2 runs Motion Cut into alien skin and a feedback tunnel with a masked doorway. Scene 3 is a row of camera filters (raw, neon edges, posterize, pixelated mp4) over Motion Cut. Scene 4 bounces shapes, a reaction‑diffusion sprite, a half‑transparent video and a hidden object over a warped YouTube backdrop with a masked window. Scene 5 is the mandala wall. Scenes are bound to MIDI notes 36‑40, four knobs are mapped (CC1 plasma speed, CC2 tunnel zoom, CC3 skin wiggle, CC7 gravity), program change is on.

### Wall Mandala — `demos/wall-mandala.json`

![Wall Mandala](demos/wall-mandala.gif)

Triptych for a wide wall: hexagon wing, kaleidoscope‑of‑plasma center, laser wing, with a mask keeping the doorway dark. Bass changes the mandala's symmetry, highs scale the lasers, beats recolor them. Scenes: Triptych, Coral (reaction‑diffusion center), Full mandala.

### Window Dodge — `demos/window-dodge.json`

![Window Dodge](demos/window-dodge.gif)

Full‑canvas physics arena with two masked windows and a masked sign. Shapes plus a reaction‑diffusion sprite and a plasma ball bounce around them, never into them. Grab any of them and throw it. Trails on, bass swells object size, beats kick everything, Space bumps the pile. Scenes: Bounce, Zero‑G pinball (stripes backdrop), Heavy rain.

### Mirror Tunnel — `demos/mirror-tunnel.json`

![Mirror Tunnel](demos/mirror-tunnel.gif)

Needs a webcam (it asks on load). Everything runs through Motion Cut, so the wall and parked cars behind you fade to black and only people moving reach the projector. Scenes: Alien skin (wiggling reaction‑diffusion grows out of your silhouette), Tunnel (six‑fold feedback, motion drives zoom, beats recolor), Neon ghost (tinted Motion Cut on the wall, you appear only while moving), Mandala, Split. The GIF above was recorded with a synthetic test camera that never stops moving, so the whole frame is lit; with a real camera only the person shows.

Rebuild them with `tests/make_demos.py` (JSON + stills) and `tests/make_gifs.py` (the GIFs). Both drive the app in headless Chrome so the files always match the current save format.

---

## Webcam, effects, and audio reactivity

- **Webcam**: press 📷 Webcam. It appears in the library like any file. Click it to put it on the selected Projection or Physics layer.
- **Effects on media**: select a layer (or a physics object) and use the "+ Effect" dropdown in the inspector, or drag an effect thumbnail onto a layer row. The effect wraps whatever the layer shows: GIF, PNG, video, webcam, pattern, or another effect. Each wrap is its own instance with its own settings, so two Corals on two layers can look different. The inspector shows the chain (`flower.gif → Reaction → Kaleido`); click a link to edit that stage, "Remove top effect" unwraps one. YouTube cannot be wrapped (browsers block reading its pixels).
- **Effects** (✨ in the pattern dropdown): Feedback / Kaleidoscope, Kaleidoscope, Reaction‑Diffusion, Motion Cut, Filter. Adding one from the dropdown uses the selected layer's media as the source, then the webcam, then the newest file. A thumbnail marked "(no source)" shows only its built‑in seed; set Source in the inspector.
  - Filter: one cheap pass with a Mode switch: edges, neon edges (colored by edge direction), posterize, threshold, pixelate, invert, solarize, false color, mirror. Amount tunes the mode. Point it at the webcam for projectable live looks.
  - Feedback: raise Feedback toward 0.99 for long trails, Zoom above 1 for a tunnel, below 1 for an implosion. Symmetry folds the image into a mandala. Edges makes the webcam a neon outline so only movement smears into the loop.
  - Reaction‑Diffusion: Feed/Kill pick the organism (0.037/0.06 = worms, 0.055/0.062 = coral, 0.03/0.057 = spots). Src seed injects the source silhouette as chemical B. Wiggle / Wiggle freq warp the whole pattern through a rolling sine field so it squirms. Rim glow lights the edges. Reset re‑seeds.
  - Motion Cut: point it at the webcam, then chain other effects off it (set their Source to the Motion Cut) so only moving people drive them. Fade time = how fast a still thing vanishes. Sensitivity = how much change counts. Hold = how long a pause is forgiven. Ghost bg leaves a faint trace of the background. Tint colors the foreground. Relearn resets the background after the camera moves.
- **Quality** (top bar: Low / Med / High): camera capture size (360p / 720p / 1080p, changed live on the running track, no re‑prompt) and the buffer size of every pattern and effect (×0.5 / ×1 / ×1.5, resized in place). Drop to Low when effects on the webcam stutter on an old laptop. Saved with the project.
- **Mic**: press 🎤 Mic. Meters show bass, mid, high, level, beat. Webcam motion shows once a webcam is live.
- **React**: in any pattern's ⚙ panel, or in the Physics Arena panel, set React = signal, choose a parameter, and an Amount (negative inverts). Example: bass → Zoom on Feedback, motion → Speed on Hexagons, beat → Size on physics.
- **On beat**: patterns can randomize hue; physics layers can kick every object with a random impulse.

Mic and webcam need a user click to start (browser permission). They are remembered in saved projects and re‑requested on load.

---

## Scale, size, and realign (inches on the wall)

Percent coordinates make a layout survive resolution changes, but on site you think in feet: "the banner has to be 8 ft tall and start 3 ft above the door". The 📏 Scale section at the top of the inspector turns stage percent into real units.

1. Go fullscreen on the projector (F, then P for the panels) so the stage has the projector's aspect.
2. Press 📏 Measure, click both sides of something you know the size of (a door is ~6'8" tall, 3' wide; a brick course is 2⅝"), type the distance in the box (`6'8"`, `80in`, `2.03m`), Enter. The app computes the width of the whole projected image and shows `1 in = N px`.
   - Or type the image width directly into Wall width if you know the throw.
3. Select any layer. Under its settings you get `on the wall 12'5" × 8'0"`, editable Width / Height (keep proportions on by default), Center X / Y from the top-left of the image, and a nudge pad. Type `8'` into Height: the quad scales about its center to eight feet. If that would push it off the stage it slides back inside instead of clipping.
4. Arrow keys move the selected layer (or physics object) by the Nudge step, Shift for ×10. Default step is 1 inch.
5. Physics objects get a Diameter field in the same units.

**Realign after a bump.** The ruler you measured stays on the stage as a yellow dashed line with two draggable ends. When someone kicks the tripod, drag the ends back onto their landmark: the scale updates. Tick *Realign: ruler drags the whole scene* first and every layer, mask, and physics object follows the ruler (move, scale, rotate), so one drag puts the whole look back on the wall. Units (ft/in, inches, cm, m), the ruler, and the nudge step are saved with the project and the autosave.

Caveat: height is derived from width via the output's aspect, so a keystoned projector lies a little vertically. Measure a vertical landmark if the vertical dimension matters more.

---

## Scenes and MIDI

**Scenes** are snapshots of your layer stack plus every pattern's settings. The media library is shared across scenes, so the same GIFs and webcam serve every look.

1. Build a look, press + Scene. Repeat for each look.
2. Click a scene pad to recall it. Keys 1–9 recall scenes by number. Double‑click to rename.
3. The active scene is live: anything you change while it is selected is written back when you switch away or save. 💾 in the inspector forces a write.
4. 📑 duplicates a scene. Use it for templates: map the room once (quads, masks, arena), duplicate, then swap the media on the copy for graduation, the next rally, whatever. The copy lands right after the original, becomes active, and has no MIDI note.

**MIDI** (Chrome/Edge, Web MIDI):

- Press 🎹 MIDI once. Devices hot‑plug.
- Scene switching: press 🎹 on a scene, then hit a pad or key. Program change messages also recall scenes by index (PC 0 = scene 1).
- Knobs: every slider in the inspector (pattern params, physics arena) has a 🎛 learn button. Click it, then move any knob or fader on your controller. The button turns green and shows the CC number; the × beside it clears. Esc cancels a learn.
- The MIDI section at the bottom of the inspector lists every binding (notes to scenes, CCs to sliders) with a × per row and Clear all.
- Scene bindings and CC maps are saved in the project JSON and in the autosave, so a controller layout survives reloads and travels with the file.

---

## Physics layer (bouncing objects)

1. Choose Physics, press + Add Layer.
2. Optional: click 3+ points to draw an arena polygon, then Complete Shape. No points = whole canvas.
3. Use the Physics Arena panel to add circles, rects, triangles, hexagons. Click any media item in the library (GIF, video, image, or pattern) to add it as a bouncing sprite.
4. Sliders: Gravity, Speed, Bounce (restitution), Size, Spin, Trails, Hardness (applies to every object). Shuffle re‑rolls positions.
5. A physics layer is a group: its objects appear as indented rows under it in the layer list. Click a row to select the object (inspector shows kind, shape, color, media, size, opacity, hardness, spin, effect chain), drag rows to change draw order, 🗑 or Delete removes it. On the stage every object gets a green outline when handles are on; the selected one also gets a scale square and a rotate handle.
6. Grab any object on the stage with the mouse (or finger) and throw it. Works with handles hidden and in fullscreen. The Bump hotkey (default Space, change it in the physics panel) shakes every object in every physics layer, biased upward so settled piles lift.

Objects never enter Mask polygons: masks act as solid walls, so blocked‑out windows, signs, and people stay clear. Use ⬠ on the layer row to redraw the arena.

Tip: Prepare multiple saved JSONs (different surfaces/messages) and load them quickly on site.

---

## Roadmap

See `ROADMAP.md` and the GitHub issues. Headline: coordination across several laptops and projectors (#2): state sync, synced scene switches, webcam-measured projector offsets, auto-alignment.

---

## Minimal hardware

- Any laptop from the last decade that runs a modern browser
- Common 720p/1080p projector (short‑throw helpful but not required)
- Optional: small tripod or clamp mount
- Extension cord and gaffer tape

No special GPU or drivers required.

---

## Controls and shortcuts

- B — Blackout output (panic key). B again restores.
- C — Kill the webcam stream (privacy). Click 📷 Webcam to restart.
- F — Fullscreen (whole page; panels hide, handles hide, screen wake lock on)
- P — In fullscreen, overlay the panels on top of the stage without resizing it, for precise alignment at output resolution. P again hides them.
- H — Toggle handles
- I — Toggle the inspector panel
- Enter — Finish placing points (same as Done)
- 1–9 — Recall scene by number
- Delete — Delete active layer. Ctrl+Z (Cmd+Z) restores it, up to 10 deep.
- Arrow keys — Nudge the selected layer or physics object by the Scale nudge step (Shift ×10). Without calibration, 0.5% of the stage.
- Space — Bump all physics objects (configurable in the physics panel)
- Esc — Cancel point placement or a MIDI learn
- Mouse or touch (pointer events, tablets work):
  - Projection: click 4 points clockwise
  - Mask / Physics arena: click 3+ points, then Complete Shape
  - Selected layer: drag the outline or center handle to move, the green square to scale, the purple circle to rotate

---

## Save/Load and autosave

- **Save** writes one JSON with everything embedded: images, GIFs, videos (as base64), patterns (as parameters), scenes, MIDI maps. Big videos make big files. The HUD reports the size. Copy it to a USB stick and it loads anywhere with nothing to relink.
- **Load** restores the file. If a media item is missing (older file without embedded data) a relink prompt lists only the missing ones; the rest load silently. You can also cancel and drop the file into the library later, it relinks by filename.
- **Autosave** runs 600 ms after any change into IndexedDB, with the original media blobs cached alongside. Nothing is re‑encoded, so it costs nothing mid‑show. On next open you are offered the recovery. If autosave ever fails the HUD says so in capitals; save a file.
- Sample projects live in `gifs/`. Old versions and the original spec are in `archive/`.

---

## Field checklist

- Charge laptop; disable auto‑updates. Fullscreen requests a wake lock, but set the OS to never sleep anyway.
- Open the page from disk or https. On a LAN `http://` address the webcam, mic, and MIDI buttons will tell you they cannot start.
- Press B once to confirm blackout works before going live.
- Set browser zoom to 100%
- Pre‑focus and keystone the projector
- Bring spare HDMI/USB‑C adapters
- Prepare dark/contrasty artwork; high‑legibility fonts
- Pack long power cable and tape
- Test fullscreen and handle toggle before moving

---

## Tips for alignment on uneven surfaces

- Place four Projection points at visually strong corners (windows, tiles, bricks)
- Use Mask layers to clip spill around edges, signs, or foliage
- For wide walls, split into multiple Projection layers with different media if needed
- Keep point order consistent (clockwise) to avoid twisted quads

---

## Safety and operational considerations

- Be mindful of surroundings; avoid shining into windows or traffic
- Keep cables tidy to prevent trips
- Consider spotters/watchers; plan quick pack‑up
- Know local guidelines and laws before operating

---

## Troubleshooting

- Nothing shows on a Projection layer:
  - Ensure 4 points, media assigned, and media finished loading. Check B is not engaged (the Black button turns red).
- GIF/Video missing after loading a JSON:
  - Older files did not embed them. Drop the original file into the library; it relinks by filename.
- A pattern or effect went black mid‑show:
  - WebGL context was lost (projector hotplug, GPU reset). It rebuilds itself when the context returns; the HUD reports both events.
- YouTube quad shows "error 153" / "Video player configuration error":
  - YouTube refuses embeds with no referrer, and a page opened from disk sends none. Serve the folder: `./serve.sh`, then open http://localhost:8000/. Also fails behind referrer-stripping extensions or privacy settings.
- Webcam / mic / MIDI button says it needs https:
  - You opened the page over plain http on a LAN. Use the file from disk or an https host.
- Physics says object cap reached:
  - 40 per layer keeps old laptops smooth. Remove some or add another physics layer.
- Output looks soft:
  - Check browser zoom and devicePixelRatio; try 100% zoom
- Seams in warped media:
  - Slightly adjust points; the renderer expands triangles to reduce gaps

---

## Technical notes

- Single HTML file (vanilla JS + inline CSS). A section index comment sits at the top of the script. Tunable constants live in one `TUNING` object.
- GIF decoding via gifler. During development it loads from a CDN; release builds inline it (see git history, commit `71039ec`). If the decoder is missing (offline dev copy) GIFs fall back to still frames with a HUD warning. Zero‑delay GIF frames are clamped to 100 ms, same as browsers, because gifler otherwise spins forever.
- Persistence: IndexedDB stores `kv/autosave` (snapshot, no media data) and `files/<kind>:<name>` (original blobs). Save embeds blobs as data URLs.
- Tests: `./tests/run.sh` drives headless Chrome through load, physics, scenes, MIDI, autosave, and a fresh‑machine Save/Load round trip. Needs `uv` and a Chrome binary. Large sample media is marked for Git LFS in `.gitattributes`.
- Patterns render into offscreen canvases (pixel generators at 128–160px, vector ones at 512px) and only tick when a layer uses them
- Effects run in their own WebGL context with ping‑pong framebuffers (feedback at 512px, reaction‑diffusion at 256px with half‑float state when available, 8 sim steps per frame)
- Audio: AnalyserNode (fft 1024), band averages with attack/release smoothing, beat = bass spike above running average with a 220 ms refractory period
- Motion: frame difference of the webcam downsampled to 48×36
- Physics: circle colliders, polygon edge collision against arena + masks, pairwise elastic collisions, 2 sub‑steps per frame
- Canvas with devicePixelRatio scaling
- Projection rendering via grid subdivision into triangles
- Percent‑based coordinates (0–100) so layouts adapt to resolution changes
- Real-world scale stores one number, the projected image width in inches (`settings.scale.wallWidthIn`); height follows the output aspect (stage in fullscreen, otherwise the screen). Lengths are parsed from `8' 6"`, `102in`, `2.6m`, `260cm` and formatted in the chosen units. The ruler is two stage-percent points plus its real length; dragging an end re-derives the width, and with Realign on applies a similarity transform (translate, uniform scale, rotate) to every layer polygon and physics object.

