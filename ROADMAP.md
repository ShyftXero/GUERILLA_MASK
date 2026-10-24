# Roadmap

Tracked as GitHub issues. This file is the short version.

## Coordination (the next big unlock) — epic #2

| # | Item | Status |
|---|------|--------|
| #3 | Sync project state across instances over LAN / hotspot, no server to install | planned |
| #4 | Multi-projector scenes, synced scene switching on the same beat | planned |
| #5 | Webcam-based projector offset calculation (one camera sees the wall, each projector flashes a pattern) | planned |
| – | Real-world scale: measure a landmark, size layers in ft/in/cm/m, nudge by inches, ruler-anchored realign of the whole scene. Foundation for #5/#6 (offsets will be expressed in the same units) | done |
| #6 | Auto-alignment and edge blending across projectors from those measurements | planned |

Order: #3 → #4, #5 → #6. #3 and #5 can be built in parallel.

## Smaller items
- Mesh warp (grid of control points) for curved or multi-plane surfaces.
- Per-output color/brightness trim.
- Scene crossfade instead of a hard cut.
- Audio from a file/track as a signal source, not only the mic.
- Soft masks for polygons with holes.

## Done recently
Patterns and GPU effects (feedback, kaleidoscope, reaction-diffusion, motion cut, filters), physics layers with grab/throw and bump, webcam(s) and URL media (YouTube, remote mp4), effect chains per layer/object, scenes with MIDI notes and CC learn, IndexedDB autosave with media cache, self-contained Save, hardness (soft edges) per layer/object/mask, stage edge fade, fullscreen panel overlay, UI scale.
