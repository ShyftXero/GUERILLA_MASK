# A true projective raster path for pro-mode faces

## Status

accepted

## Context

The existing raster warp (`renderQuad`) subdivides a quad into an 8×8 grid and bilinearly interpolates the four corners. Under steep perspective this bows straight source lines — tolerable for loose VJ content, wrong for pro-mode surface-aligned projection, where media must sit *flat* on a physical face viewed at an angle.

## Decision

Pro-mode face quads render through a new **projective** raster path that uses a real unit-square→quad homography (the adjugate method already in the file as `matrix3dFromQuad`), so straight lines stay straight on the face. The bilinear path stays as-is for ordinary projection layers; the projective path is used only for pro-mode faces.

## Considered options

- **Reuse the bilinear quad.** Rejected: it bows exactly in the pyramid/steep-angle case that pro mode exists to serve, undercutting the feature's whole point.

## Consequences

- Two warp paths coexist. The projective path is per-face and more expensive, so it is reserved for pro mode rather than made the default.
- The homography math is already in-file; this is a new raster loop consuming it, not new math.
- Adjacent faces must share ridge vertices so their projective quads meet without a seam (see GLOSSARY: **Ridge**).
