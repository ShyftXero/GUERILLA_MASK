# GUERILLA_MASK

A single-file, no‑frills projection‑mapping tool designed for rapid deployment during demonstrations and pop‑up actions. Works offline in a modern browser, on modest laptops, with common projectors. Map images/GIFs/videos onto surfaces, cut holes with masks, and add quick marker notes. Save/load projects as JSON for reuse.

![guerilla_mask ui ](showoff.gif "the page")

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
  - Marker: freehand strokes for quick notes/markups
- Media: images, GIFs (via gifler), videos
- Layer reordering, selection, delete
- Global Play/Pause, Toggle Handles, Fullscreen
- Save/Load project as JSON
  - Images embed in JSON
  - GIF/Video saved as filename stubs; re‑link on load
- HUD that auto‑hides in fullscreen to keep output clean

---

## Quick start (field workflow)

1. Download/open the single HTML file in Chrome/Firefox/Safari.
2. Click Upload and add your media (PNG/JPG, GIF, MP4).
3. Choose Projection, press + New Layer, then click 4 points on the surface in the live view.
4. Use Set Media on that layer to assign your file.
5. Add Mask layers to hide unwanted spill on surroundings.
6. Use Marker layer for quick alignment notes or arrows.
7. Press Fullscreen; toggle handles off before you go live.

Tip: Prepare multiple saved JSONs (different surfaces/messages) and load them quickly on site.

---

## Minimal hardware

- Any laptop from the last decade that runs a modern browser
- Common 720p/1080p projector (short‑throw helpful but not required)
- Optional: small tripod or clamp mount
- Extension cord and gaffer tape

No special GPU or drivers required.

---

## Controls and shortcuts

- H — Toggle handles (for Projection/Mask)
- Space — Play/Pause all GIFs/videos
- F — Fullscreen stage
- Delete — Delete active layer (if enabled)
- Mouse:
  - Projection: click 4 points (clockwise)
  - Mask: click 3+ points, then “Complete Mask”
  - Marker: press/drag to draw; color via picker

---

## Save/Load and media relinking

- Save creates a JSON with full project state.
- Load restores layers and geometry.
- Images embed; GIFs/videos are stored by filename only.
- After loading, re‑upload the same GIF/video filenames to relink them; layers keep their references.

---

## Field checklist

- Charge laptop; disable sleep and auto‑updates
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
  - Ensure 4 points, media assigned, and media finished loading
- GIF/Video silent after loading a JSON:
  - Re‑upload the original file to relink (same filename)
- Output looks soft:
  - Check browser zoom and devicePixelRatio; try 100% zoom
- Seams in warped media:
  - Slightly adjust points; the renderer expands triangles to reduce gaps

---

## Technical notes

- Single HTML file (vanilla JS + inline CSS); optional gifler via CDN for GIFs
- Canvas with devicePixelRatio scaling
- Projection rendering via grid subdivision into triangles
- Percent‑based coordinates (0–100) so layouts adapt to resolution changes

