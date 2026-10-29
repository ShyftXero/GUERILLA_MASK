# GUERILLA_MASK

Projection-mapping / VJ tool: lay warped media, patterns, and masks over a physical scene via a projector. This glossary covers the shared language of the app, with the **structured-light mapping** feature (webcam-assisted auto-mapping) as its current growing edge.

## Language

### Mapping surface

**Map**:
The one-shot action of sensing a physical object with the webcam and emitting layers that fit it. Produces an occlusion mask and, in pro mode, surface-aligned projections.
_Avoid_: scan, capture, detect

**Calibration**:
Establishing how the camera's view relates to the projector's output, so anything seen in the camera can be placed correctly on the wall. Produced once per rig setup, re-run only when the camera or projector moves. The stored relation is written `H_cp` (camera→projector).
_Avoid_: alignment, registration, setup

**Difference masking**:
Isolating an object by comparing a camera frame of the scene lit black against one lit white; the pixels that changed are the lit object.
_Avoid_: segmentation, keying, subtraction

**Camera underlay**:
The live webcam feed shown beneath the layers in the editor, so a person maps on-screen against what the camera sees instead of looking at the physical wall.
_Avoid_: preview, backdrop, video layer

**Pro mode**:
The advanced mapping path that recovers an object's separate faces (e.g. the two visible sides of a pyramid) and aligns a projection to each, rather than just masking the object's outline.
_Avoid_: 3D mode, advanced, expert

**Face**:
One flat side of a physical object that gets its own surface-aligned projection in pro mode.
_Avoid_: plane, facet, side

**Ridge**:
The shared edge where two faces meet, found in pro mode as an abrupt slope change in the projected grid. Adjacent faces share its vertices exactly so their projections meet without a seam.
_Avoid_: edge, crease, seam, fold

### Layers (existing model)

**Layer**:
One entry in the ordered stack that composites into the output. Its geometry is a list of points in canvas space. Every layer is one of three kinds below.
_Avoid_: object, element, shape

**Occlusion mask layer**:
A mask-kind layer: a polygon that subtracts from the output (and blocks physics). An auto-mapped object's outline becomes one of these.
_Avoid_: stencil, clip, cutout

**Surface-aligned projection**:
A projection-kind layer whose four corners are placed so its media sits flat on one physical face.
_Avoid_: warp layer, mapped quad

### Spaces

**Canvas space**:
The editor/output coordinate system, expressed as percentages (0–100) of the canvas. In this app it is identical to **projector space** — the stage *is* the projector output. Layer points live here.
_Avoid_: screen space, stage space, output space (as distinct things — they are the same)

**Camera space**:
The webcam image's pixel coordinate system. Distinct from canvas/projector space because the camera and projector view the scene from different places; `H_cp` converts between them.
_Avoid_: image space, webcam coords
