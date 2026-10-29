# Camera→projector calibration precedes object detection

## Status

accepted

## Context

The structured-light "Map" feature senses a physical object with a webcam and emits layers that fit it. A detected object silhouette lands in **camera space** (webcam pixels), but layers render in **canvas/projector space**. The camera and projector view the scene from different positions, so a silhouette cannot be drawn to the wall as-is — the parallax between the two viewpoints would shift it.

## Decision

Calibration is step zero of the feature, not an optional refinement. Before any object detection, we establish a camera→projector homography `H_cp` by briefly projecting a known pattern (a bright quad / small grid) and locating it in the webcam frame. Difference masking, the camera underlay, and pro-mode face mapping all read from `H_cp`. It is stored on the global `app` state (alongside the existing `app.scale`) and re-run only when the rig moves.

## Considered options

- **Assume the camera is co-axial with the projector and skip calibration.** Rejected: lens axes never coincide exactly, so content would land off the object. Brittle and un-tunable.
- **Full temporal structured light (Gray code / phase shift) from the start.** Deferred: yields a dense per-pixel map but needs many projected frames, a steady scene, and controlled ambient light, and the app's raster path has no true projective/mesh warp to consume it yet. Too much failure surface for v1.

## Consequences

- A single planar `H_cp` is exact only for surfaces near the calibration plane. Wall-flush features (doorframes, flats, projected-onto walls) map faithfully; objects standing proud of the plane (a column, a pyramid) carry parallax error at their silhouette — which is precisely why multi-face recovery is **pro mode**, not v1.
- The one-shot Map assumes the camera and projector stay still after calibration; moving either invalidates `H_cp` and requires re-calibration.
