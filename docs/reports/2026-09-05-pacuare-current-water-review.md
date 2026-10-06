# Pacuare / Upper Huacas water review — 2026-09-05

Scope: the actual `/Game/RaftSim/Maps/L_UpperHuacas` gameplay scene, not the
separate opaque preview material. This is a 600 m interpreted reach, not a
survey-accurate reconstruction of Upper Huacas. No hydraulic cook, terrain,
raft forces, or collision settings were changed in this pass.

## Findings and changes

The launch and 310 m drop-pool baseline captures showed a smooth reflective
sheet with directional streaks and broad bands. Runtime telemetry reported
maximum aeration 0.2188. With runtime intensity 0.9, the inherited material's
0.28 cutoff removed even that maximum before the foam coverage stage.

- Added an isolated `M_RaftSim_PacuareCurrentWaterV2` parent to the existing
  live-volume instance. The parent preserves the single visible surface,
  raft aperture, cooked free-surface geometry, and existing depth-gated
  displacement. It does not add a second foam mesh.
- Replaced the active directional texture-normal input with two rotated
  procedural gradient scales, advected by the existing integrated-current
  collection. Pixel-footprint filtering suppresses subpixel glints. This is
  optical detail, not a new fluid simulation or local eddy solver.
- Set the aeration cutoff to 0.06, coverage gain to 4.5, and white core gain
  to 1.8. Speed-only whitening is disabled: fast, unaerated water stays water.
- Reduced Pacuare's single-surface presentation subdivision from six to
  three (0.5 m to 1 m spacing). The hydraulic data and solver resolution are
  unchanged. This budget is scoped to Pacuare's one-surface path.
- Extracted the already-reviewed Hance gradient shader into a shared
  authoring helper with river-specific parameters. Hance's shader text and
  calibration remain unchanged; its assets were not refreshed for this pass.

## Validation protocol

Real engine captures use `review_pacuare_water.ps1`: 1280×720 offscreen
gameplay, raft walked to stations 24, 280, 310, and 380 m, followed by an
eight-frame series. No generated reference images stand in for gameplay.
`review_pacuare_water_assets.py` checks the saved parent, actual Normal
connection, shader inputs, and aeration cutoff.

Performance is a short engineering diagnostic: Development editor-hosted
game, same map launch, 1280×720, saved 87% screen percentage and medium
quality, 12 seconds warmup followed by 20 seconds sampling. This is not a
packaged-release qualification or an identical replay trajectory.

## Results

Build passed. All four station walks and eight-frame capture series completed
without material compilation failure. The saved-graph audit passed, and the
focused Unreal test `RaftSim.M9.FPacuareLiveTransmittingWater` passed (one test).
An additional eight-frame pool capture from the opposite side completed, and
Colorado's saved material passed its read-only audit after the shared-code
refactor.
Twenty-two focused Python test functions passed when invoked directly with
`runpy`; pytest is unavailable in this runtime. These include Pacuare source
contracts/provenance plus shared current-normal and single-surface guards.
They are not a full test-suite run or visual acceptance.

The older hash-locked transmitting-water review has two stale provenance-JSON
hashes. The PNG source hashes still pass. Historical evidence was not rewritten
to pretend that the old review represents today's material.

| Diagnostic | Before | After |
| --- | ---: | ---: |
| Presentation vertices | 92,833 | 23,377 |
| Presentation triangles | 184,320 | 46,080 |
| Initial mesh refresh, ms | 66.7–74.2 | 17.8 |
| Mean wall-clock frame, ms | 65.29 | 12.14 |
| FPS derived from mean wall time | 15.3 | 82.4 |
| 95th-percentile wall frame, ms | 69.17 | 24.54 |
| Maximum wall frame, ms | 76.45 | 36.16 |
| Frames over 33 ms | 293 / 307 | 1 / 1,648 |
| Mean solver step, ms | 2.23 | 2.48 |

Both runs **fail** the strict frame and solver budgets; memory passes. The
improvement is large, but these short offscreen measurements do not establish
sustained 60 FPS in a packaged game. Per-frame screenshot readback was not
running during the performance measurement. Timing/trajectory differences mean
the change cannot be attributed exclusively to mesh vertex count.

## Visual and animation review

The final approach, constriction, and runout show irregular moving ripple
highlights instead of the baseline's fine directional streak texture. The
pool keeps a calmer foreground with more activity around it. Early and late
pool frames show evolving highlights without an obvious second surface or
whole-surface on/off jump in this short sample. This does not prove the absence
of flashing over a full run. The shared current displacement drives the new
normal field; no independent scrolling clock was added.

This is **not photoreal acceptance**. Broad milky highlights and smooth areas
remain, particularly at the drop pool. The captures do not yet show convincing
overturning crests, recirculating foam volume, or airborne breaking spray.
The retained hydraulic relief peak is approximately 0.184 m; the presentation
does not manufacture metre-high waves from that field. Current advection is
the existing shared displacement, not a newly resolved per-pixel eddy field.

Some bank vegetation still intersects water and the straight, interpreted
terrain is visibly artificial. Coarsening the render lattice is a measured
performance tradeoff, not a claim of finer crest geometry. No new rectangle
popping or detached shore wave was obvious in the reviewed frames; a full-reach
shoreline traversal and a long animation capture remain open validation gates.

## Retained gameplay evidence

All PNGs below are original engine captures. Full eight-frame sequences remain
under `unreal/Saved/Screenshots/pacuare_after_*`; the repeatable capture and
asset-audit scripts are under `unreal/Scripts/`.

- [Approach before](images/2026-09-05-pacuare-current-water/approach-before.png)
  and [after](images/2026-09-05-pacuare-current-water/station-24.png).
- [Constriction, 280 m](images/2026-09-05-pacuare-current-water/station-280.png).
- [Pool before](images/2026-09-05-pacuare-current-water/pool-before.png),
  [after](images/2026-09-05-pacuare-current-water/station-310.png), and
  [later frame](images/2026-09-05-pacuare-current-water/pool-later.png).
- [Runout, 380 m](images/2026-09-05-pacuare-current-water/station-380.png).
- [Pool from the opposite side](images/2026-09-05-pacuare-current-water/pool-opposite.png).
- [Before timing](images/2026-09-05-pacuare-current-water/performance-before.json),
  [after timing](images/2026-09-05-pacuare-current-water/performance-after.json), and
  [saved material audit](images/2026-09-05-pacuare-current-water/material-audit.json).
