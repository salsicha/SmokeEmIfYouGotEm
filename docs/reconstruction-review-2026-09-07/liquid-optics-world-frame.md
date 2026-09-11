# Liquid optics and coordinate-frame corrections — September 8, 2026

Status: transient review candidates only. No production promotion, photographic
acceptance, foam simulation or gameplay performance claim.

Read-only inspection of the active template graph identified three separate
problems. The copied material instance still has the template's original parent.

1. The Single Layer Water scattering output multiplies the scattering coefficient
   by the sampled whitewater channel and the `Whitewater` scalar. The actual MID
   has `Whitewater=0`, so ordinary water scattering is zero as well. Raising
   opacity to one bypasses that problem by making a diffuse coating, not by
   producing foam. Roughness was a constant zero.
2. The raymarcher returns a grid-local SDF normal directly to the material's
   world-space normal input (`bTangentSpaceNormal=0`). This patch has a 158.435°
   grid yaw, so its lighting/reflection directions were wrong.
3. Its depth comparison divides scene depth by a dot product of local ray
   direction and world camera-forward. For the fixed oblique camera, that dot
   product is negative despite looking at the fluid. The final depth test then
   discards the valid water hit. The overhead view concealed this frame error.

`RaftSimLiquidOptics.h` creates a transient material copy. The base-scattering
candidate connects RGB scattering times its coefficient directly to the water
output, independent of foam. Roughness is exposed separately with a source-
preserving zero default. An additional candidate rotates normals using the
actual `LocalToWorld0..2` grid parameters. The final candidate uses world ray
direction in the world camera-depth comparison. No new plane, normal texture,
displacement, source, particle deletion or physics modification is introduced.

The installer refuses non-transient systems/material instances. It preserves
effective uniform parameters when reparenting the copied MIC, including volume
texture bindings. Engine template assets are never edited or saved. Inspection
exports containing engine template source are local diagnostics, not release
assets for redistribution.

## Actual rendered comparisons

All captures hold the initial camera fixed, run 12 simulated seconds, then freeze
the simulation before changing optical controls. Thus the comparisons do not
change the camera after freezing its camera-facing emitter.

- `liquid-optics-opacity-exposure`: 12 opacity/exposure controls. Transparent
  water remains nearly black; opaque water becomes painted-looking geometry.
  Capture completes in 29.912s wall time.
- `liquid-optics-base-scattering`: opacity remains zero, roughness is 0.12,
  scattering multiplier is 0.0001/0.001/0.01 per cm, and exposure bias is
  -10/-12/-14. Actual MID readback confirms the controls. Visible blue-green
  water replaces the black/opaque extremes. Completes in 36.010s.
- `liquid-optics-world-normal`: world-space normal correction changes the
  highlight directions in the overhead view. It does not solve oblique
  disappearance on its own.
- `liquid-optics-world-normal-oblique`: retained failure. The valid 12s capture
  shows terrain without the liquid because the mixed-frame depth test rejects
  it. This is not a dry simulation or successful water rendering.
- `liquid-optics-world-frame-oblique`: the corrected world-space depth test
  restores the liquid in that same oblique view. The visible patch has real
  depth, but is glossy/cyan with exposed computational edges and no convincing
  aeration or breaking-water breakup. It is not an accepted river scene.

The diagnostic light rig and exposure controls are not photographic calibration.
Blocking readbacks/manual stepping are not gameplay frame-time measurements.
Scattering strength is not a measured turbidity value. The rectangular patch is
the bounded experiment, not an acceptable shipping shoreline.

## Regression and remaining work

The first base-scattering engine suite has 10 clean passes (17.768s). The initial
world-normal regression crashed after discovering an extra empty input created
by the Custom expression constructor. The installer now clears that default
input before adding its four connected inputs; the regression returns safely
on malformed input. That failed run remains in `EngineLiquidWorldNormal.log`.
The final `engine-liquid-world-frame/index.json` has 10 clean passes, zero
warnings/failures (17.940s). It covers the connected four-input normal transform,
the mixed-frame ray-depth regression, source preservation and the existing
liquid variants. The focused Python suite has 26 passes, including the separate
exchange diagnostic. The corrected oblique GPU capture also completes; the
restored surface is visibly unsuitable for photographic acceptance.

Continue calibrated 3D storage/exit accounting and physical flow validation,
surface aeration/foam transport and breakup, full-scene single-surface coupling,
continuous motion and real-time performance. The South Fork route/rapid evidence
and the entire ordered river/crew/normalization/release queue remain open.
