# Isolated feature lab — first iteration, 2026-09-29

## Scope and status

New standalone Blender environments, not the full river or packaged game.
The full goal remains open: no water feature is physically/visually accepted.
The first deliverable is a three-second waterfall prototype clip; the two hole
boundary-condition trials have not produced an acceptable hole.

Delivered: `docs/water-feature-lab/waterfall-prototype-v1/feature.mp4` and
lossless animated preview `feature.png`. Actual rendered frames 96..166,
stride 2: 36 frames at 12 fps, 3 seconds, normal simulation speed. MP4 decoded
frame count verified; every APNG frame matched its source exactly; zero
identical adjacent frames. Repeating the preview is not a seamless simulation
loop. Representative beginning/middle/end frames were visually inspected.
MP4 SHA-256: `f4dfa15119152a12c780b21046907b6055f2a56f33fc70905300d19bc208ec7a`.

No existing game source, captured terrain, or river package was modified by
this feature-lab work. New scenes and caches live under `tmp/water-feature-lab`.
No AI-generated imagery is used as simulation evidence.

## Reproducibility

- Builder: `unreal/Scripts/build_water_feature_lab.py`.
- Cached-mesh renderer: `unreal/Scripts/render_water_feature_lab.py`.
- Particle diagnostic: `unreal/Scripts/audit_water_feature_lab.py`.
- Free-fall calibration: `unreal/Scripts/calibrate_water_feature_velocity.py`.
- Verified-frame MP4/APNG encoder: `physics/scripts/encode_water_feature_clip.py`.
- Blender 5.2.0 LTS; 6 × 1.6 × 2.9 m domain; resolution 80 (~7.5 cm cells).
- Fixed orthographic camera; 24 simulation frames/s; 168 baked frames.
- Nominal inlet values are **not measured flow rates**. The level drain is an
  artificial tailwater control, not a characteristic open-channel boundary.
- Side walls are closed; the front wall is invisible for inspection. The
  exposed vertical liquid face is therefore a cutaway, not an unsupported wall
  of water. Interpret this as a laboratory flume, not a natural free waterfall.

Waterfall command arguments: `--case waterfall --resolution 80 --frames 168
--output tmp/water-feature-lab/waterfall-v1 --bake`.
Hole v1 uses `--case hole`; hole v2 adds `--tailwater 0.65` and a new output.
Output directories must not already exist.

## Waterfall

1.2 m ledge, nominal 0.32 m upstream depth, 1.6 m/s source setting, 0.45 m
tailwater setting. Data, mesh and secondary particles all baked successfully
in 153.31 seconds. This is offline simulation time, not real-time performance.

First render was rejected: 12 mm secondary-particle display radii made the
water look uniformly white. The revised render uses 3 mm foam/spray and
1.2 mm bubble instance radii. These are explicit subgrid visual approximations,
not measured bubble sizes. Underlying liquid dynamics were not changed.

The revised stills show a connected falling sheet and changing impact surface.
Remaining visible issues include coarse, smooth sheet/crest structure, an
upstream inlet hump, artificial cutaway boundaries and uncalibrated froth.
The camera needs a complementary close view before fine visual acceptance.

Calibrated particle samples at frames 96/120/144/168:

| Quantity | Approximate measured range |
|---|---|
| Approach mean downstream velocity | 1.50–1.52 m/s |
| Approach mean vertical velocity | −0.59 to −0.61 m/s |
| Falling-region mean vertical velocity | −1.88 to −1.92 m/s |
| Pool upper-band mean downstream velocity | +0.03 to −0.23 m/s |
| Sampled lower-band mean downstream velocity | +0.47 to +0.56 m/s |

These support downward acceleration and some pool return motion, but are NOT
a validated trajectory, discharge budget, turbulent roller or convergence
study. Narrow-band FLIP particles do not sample the deep interior uniformly.
Fixed regions include mixed flow. The liquid reconstruction volume changes
during the clip; a net mass balance with inlet/outlet flux is still required.

## Hole trials: not accepted

Both use a 0.35 m drop, nominal inlet depth 0.30 m and velocity setting 3 m/s.
The 0.85 m tailwater trial was visibly submerged and indistinct. Lowering the
level drain to 0.65 m did not establish the required upstream surface roller.
At frames 96/120/144/168, the v2 sampled surface mean flow stays downstream
(~0.27–0.37 m/s); sampled approach speed is only ~0.52–0.60 m/s, not the
3 m/s source setting. Do not treat the configured inlet Froude as actual flow.

Next: diagnose/replace the flooded source boundary, measure actual section
flux and tailwater stage, and use a deliberately controlled jet/flume.
Do not cosmetically paint a roller onto this failed flow field.

## Velocity-readback calibration

The first `kinematics.json` files incorrectly labeled Blender API raw velocity
as m/s. They are explicitly superseded by `kinematics-v2.json` (raw labels)
and `kinematics-calibrated.json` (additional estimated m/s fields).

A separate initially stationary liquid sphere falls without contact for
12 frames in the same-size/resolution domain. The fitted centroid acceleration
is −9.82931 m/s² versus gravity −9.80665 m/s² (0.231% relative error), maximum
quadratic position residual 0.527 mm. The inferred raw-velocity scale is
14.97107. This calibration passed its 5% gravity / 1 cm residual checks.
It covers only the installed build and matching domain/time/resolution.
It does not certify the hydraulic boundary, mass conservation or appearance.

## Remaining cases

Standing waves, boulder pillows, eddies, boils, isolated surface foam and
isolated aerated froth/spray are still to be built, rendered and validated.
The waterfall's secondary particles do not count as those separate cases.
Follow the complete acceptance matrix in `docs/plans/isolated-water-features.md`.
