# Projection Mapper (Single‑file Web App)

A lightweight projection‑mapping tool in one HTML file. Map images/GIFs/videos onto quads, add polygon masks, and scribble quick annotations with a simple Marker layer. Save and load full projects as JSON. No frameworks.

---

## Features

- Single HTML file; no build step
- Three layer types:
  - Projection: 4‑point quad with bilinear subdivision and per‑triangle affine mapping
  - Mask: polygon that cuts holes in the composite (destination‑out)
  - Marker: freehand scribbles; one color per layer; no transforms
- Media library with Images, GIFs (via gifler), and Videos
- Layer reordering, selection, delete
- Play/Pause all animated media, fullscreen mode with HUD auto‑hide
- Project save/load (JSON). Images embed; GIF/Video are filename stubs that can be re‑linked later.

---

## Quick start

1. Download/open the HTML file in a modern browser (Chromium, Firefox, Safari).
2. Upload media (images/GIFs/videos).
3. Choose a layer type (Projection, Mask, Marker), then press “+ New Layer”.
4. Draw:
   - Projection: click 4 points (clockwise) on the canvas.
   - Mask: click 3+ points, then “Complete Mask”.
   - Marker: press/drag to scribble; choose color from the color picker (applies to active Marker layer).
5. Reorder layers from the Layers list.
6. Assign media to a Projection layer using “Set Media”.
7. Save as JSON. Load later; re‑upload matching GIF/Video filenames to re‑link.

---

## UI map

- Sidebar
  - Project: Save, Load, “Loaded:” hint
  - Media Library: upload input and list with Use buttons
  - Layer Type: Projection, Mask, Marker + “+ New Layer”
  - Layers: list with Up/Down/Select/Set Media/Delete, plus “Complete Mask” and “Clear All Layers”
  - View & Playback: Toggle Handles, Play/Pause All, Fullscreen, Marker Color
- Stage
  - Top bar: canvas size, active layer, status
  - Canvas: final composite
  - SVG overlay: handles/paths for Projection/Mask
  - HUD: status/active; auto‑hides in fullscreen after inactivity

---

## Controls and shortcuts

- C: toggle sidebar (via “Hide” button)
- H: toggle handles (Projection/Mask only)
- Space: play/pause all videos/GIFs
- F: fullscreen stage
- Delete: delete active layer (if implemented in your build)
- Mouse/Touch:
  - Projection: click to add 4 points
  - Mask: click 3+ points, then “Complete Mask”
  - Marker: press/drag to draw; color via color picker

---

## Layers

- Projection
  - 4 points in percentage coordinates (0–100)
  - Requires assigned media
  - Drawn with bilinear subdivision into triangles to minimize distortion
- Mask
  - 3+ points polygon; uses destination‑out composite to cut holes
- Marker
  - Strokes stored as arrays of percentage points
  - One color per layer (default #ffeb3b)
  - No transforms; delete the layer to “undo” all scribbles

Z‑order follows the list order: topmost row draws last.

---

## Media library

- Accepts: image/*, video/*, .gif
- Images: embedded as data URLs and immediately renderable
- GIFs: decoded using gifler into an offscreen canvas
- Videos: HTMLVideoElement; looped, muted, and plays inline
- “Use” selects a media item for assignment to a Projection layer

---

## Save/Load behavior

- Save: downloads a project JSON file named “projection-project-YYYY-MM-DDTHH‑MM‑SS.json”
- Load: replaces current state; images are hydrated from data URLs
- GIF/Video: saved as filename stub; after load, they appear as “relink needed”
  - To relink: upload the same filename and kind; the app hydrates the stub and keeps layer references intact

### JSON schema (representative)

```json
{
  "version": "1.2.0",
  "savedAt": "2025-10-24T12:34:56.000Z",
  "media": [
    { "id": "m1", "name": "image.jpg", "kind": "image", "type": "image/jpeg", "data": "data:image/jpeg;base64,..." },
    { "id": "m2", "name": "loop.gif",  "kind": "gif",   "type": "image/gif", "filename": "loop.gif" },
    { "id": "m3", "name": "clip.mp4",  "kind": "video", "type": "video/mp4", "filename": "clip.mp4" }
  ],
  "layers": [
    {
      "id": "l1",
      "type": "projection",
      "name": "Projection",
      "points": [{ "x": 10, "y": 10 }, { "x": 80, "y": 12 }, { "x": 78, "y": 60 }, { "x": 12, "y": 58 }],
      "mediaId": "m1",
      "mediaName": "image.jpg",
      "playing": true
    },
    {
      "id": "l2",
      "type": "mask",
      "name": "Mask",
      "points": [{ "x": 30, "y": 30 }, { "x": 50, "y": 30 }, { "x": 40, "y": 50 }],
      "playing": true
    },
    {
      "id": "l3",
      "type": "marker",
      "name": "Marker",
      "strokes": [
        [{ "x": 20, "y": 20 }, { "x": 25, "y": 22 }, { "x": 30, "y": 25 }],
        [{ "x": 40, "y": 40 }, { "x": 45, "y": 45 }]
      ],
      "color": "#ffeb3b",
      "playing": true
    }
  ]
}
```

Notes:
- Percent coordinates are clamped to [0, 100] and are relative to the current canvas size.
- Deleting a layer removes its content; there is no per‑stroke undo for Marker.

---

## Fullscreen and HUD

- Fullscreen targets the stage for clean output
- HUD shows “Status” and “Active”
- In fullscreen, HUD auto‑hides after short inactivity; any mouse/touch/keyboard activity re‑shows it
- Exiting fullscreen restores HUD visibility

---

## Rendering details

- Canvas uses devicePixelRatio scaling; size readout shows “WxH @dprx”
- Image smoothing enabled and set to high
- Projection mapping:
  - Subdivide quad into SUBDIV×SUBDIV grid (default 10×10)
  - Split each cell into two triangles
  - Compute affine transform per triangle; clip and draw
  - Slightly expand destination triangles to hide seams

---

## Relinking flow (GIF/Video)

1. Load a saved project; GIF/Video items show as stubs marked “relink needed”
2. Upload the original files with the same filenames
3. The app hydrates the stubs in place (IDs preserved); projection layers start rendering again

---

## Troubleshooting

- Nothing renders on a Projection layer:
  - Ensure 4 points are set, media assigned, and media is “ready” (image loaded, GIF canvas created, or video metadata loaded)
- GIF/Video not playing after load:
  - Re‑upload the original file to relink
- Canvas looks soft:
  - Check browser zoom and devicePixelRatio; the app scales for DPR automatically
- Handles missing:
  - Toggle “Toggle Handles” (H). Marker layers do not have handles.

---

## Development notes

- Vanilla JS; no frameworks
- External dependency: gifler via unpkg for GIF decoding
- SVG overlay handles for Projection/Mask; Marker uses direct freehand capture
- Data model:
  - uploadedFiles: media store (image/gif/video)
  - layers: ordered array of projection/mask/marker records
  - activeLayerId, layerType, handlesVisible, controlsVisible, videosPlaying

---

## Roadmap (optional)

- Delete key to remove active layer
- Snap‑to‑grid toggle for handles
- Export PNG of current canvas

---

## License

MIT (or your preferred permissive license). Include third‑party license notice for gifler if required.