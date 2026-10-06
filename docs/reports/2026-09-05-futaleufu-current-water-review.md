# Futaleufú / Terminator water review — 2026-09-05

Result: retained optical and performance improvement, **not photoreal acceptance**.
Examined actual `/Game/RaftSim/Maps/L_Terminator` gameplay, not the separate
static preview material. No terrain, hydraulic cook, raft forces, collision,
lighting, or map asset was changed in this pass. Existing unrelated edits
were preserved. Nothing was committed or pushed.

## Findings and implementation

The baseline hole capture was a dark blue sheet with subdued surface detail.
The live map already had one visible water surface. Its measured initial
aeration maximum was 0.2614, below the inherited material cutoff after the
runtime 0.9 intensity multiplier: `0.2614 * 0.9 - 0.28 < 0`.
The 92,833-vertex presentation mesh also took 90.8 ms for its first refresh.

- Added an isolated `M_RaftSim_FutaleufuCurrentWaterV5` parent to the existing
  `MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3` instance. Saved both assets
  and refreshed their existing texture dependencies. The capture-only water
  remains unchanged.
- Replaced the active normal-texture input with two rotated, current-advected
  procedural gradient scales. Pixel-footprint filtering suppresses subpixel
  detail; the existing integrated current displacement supplies motion, not
  an independent time-based panner.
- The first square-grid gradient candidate produced conspicuous pool bands.
  Flattening the mesh normals left them visible; disabling the material normal
  removed them. Reducing amplitude alone left the pattern visible. Rejected
  that candidate and introduced a Futaleufú-only triangular gradient kernel
  with a 0.22 normal-strength override. Other river variants retain their
  previous shader code. The final pool is less regularly patterned, though
  its highlights are still stylized.
- Changed foam cutoff to 0.07, coverage gain to 3.5, and white core gain to 1.8.
  Disabled speed-only whitening. This reveals existing resolved aeration; it
  does not generate new entrained-air volume or paint calm current white.
- Shifted the live shallow/deep/scattering palette away from cobalt blue
  toward blue-green. [Chile Travel's Futaleufú reference](https://chile.travel/en/attractions/futaleufu/)
  describes turquoise water; this was a qualitative color guide, not a sampled
  photometric calibration, measured turbidity model, or footage-derived match.
- Capped the single-surface Futaleufú presentation at one-metre vertices,
  reducing mesh size by about 75%. Hydraulic sampling, existing relief,
  obstacle wakes, local displacement and boat coupling remain active. No
  second water/foam surface was added.

## Gameplay inspection

Captured eight-frame series at launch/approach 24 m, entry 150 m, main hole
300 m, and recovery pool 480 m, plus opposite-side views starting at 180 m
and 320 m. These are requested walk destinations; the raft continues drifting
during the eight-second settle and capture period. They are not frozen exact
station or exact-trajectory comparisons. All six walks and captures completed
without material compilation failure.

The final rapid views show denser irregular ripple highlights and sparse
froth/spray cues. The early/late main-hole frames show the surface pattern
evolving while the raft moves. There is no obvious whole-surface toggle or
second sheet in those short sequences. This is a sampled-frame inspection,
not proof of temporal stability over a whole run or a high-frame-rate video
analysis. The original hydraulic relief peak remains approximately 0.512 m.

The following remain open:

- The rapid still lacks the curling, collapsing crests and dense recirculating
  froth needed for convincing big whitewater. Fine highlights are not foam
  volume. Sparse vertical spray streaks remain visibly artificial.
- Smooth broad pool areas, some patterned highlights, and occasional angular
  surface transitions remain. The new shader does not repair hydraulic shock
  pits documented in the September 2 inspection; those were not recooked here.
- The 600 m straight interpreted corridor and its hard end are not a
  survey-accurate reconstruction of Terminator. Shoreline quality needs a
  full-reach traversal beyond these six starts.
- This normal field uses shared integrated-current advection, not a new
  per-pixel eddy simulation. Existing foam advection is retained. Neither
  normal detail nor material color changes establish accurate raft dynamics.

## Performance

Same protocol before and after: editor-hosted Development game, offscreen
1280×720, saved 87% screen percentage, medium quality, normal map launch,
12 s warmup and 20 s sample. No captures or build ran concurrently with the
performance test. Both retained 27 production Niagara components and reported
six active aerosol plus six active roller sites. This is an engineering
diagnostic, not packaged-release qualification or an identical replay.

| Metric | Baseline | Final |
| --- | ---: | ---: |
| Presentation vertices | 92,833 | 23,377 |
| Presentation triangles | 184,320 | 46,080 |
| Initial mesh refresh, ms | 90.76 | 23.21 |
| Mean wall frame, ms | 106.90 | 14.81 |
| FPS derived from mean wall frame | 9.4 | 67.5 |
| 95th-percentile wall frame, ms | 112.67 | 33.89 |
| Maximum wall frame, ms | 118.85 | 37.43 |
| Frames over 33 ms | 188 / 188 | 153 / 1,351 |
| Mean solver step, ms | 2.80 | 3.07 |

Both runs **fail** the project's strict frame and solver budgets. Memory
passes. Average FPS improved substantially, but slower frames remain near
30 FPS and the solver still exceeds its 1.6 ms budget. Do not describe this
as a sustained 60 FPS pass or attribute every millisecond exclusively to the
mesh reduction.

## Tests and reproducibility

- Development build passed; saved material audit confirms the isolated
  parent, actual Normal connection, 0.07 cutoff, triangular-gradient calls,
  current displacement and pixel-footprint filtering.
- Unreal `RaftSim.M9.FFutaleufuTerminatorWater`: **passed**, one test.
- Focused plain-function Python runner: **30/33 passed**. All 23 current-water
  and shared presentation checks passed, including finite-difference and
  triangle-boundary continuity checks for the new analytical gradient.
  Three historical hash-locked reviews failed: depth attenuation V2,
  rapid lace V1, and transmitting water V3. Their old evidence hashes were
  not rewritten. Exact tracebacks are retained below. This is not a full
  pytest or engine automation-suite run.
- Scripts: `unreal/Scripts/review_futaleufu_water.ps1`,
  `review_futaleufu_water_assets.py`, and `review_futaleufu_water_tests.py`.
  Asset audit only saves when given `-RaftSimRefreshFutaleufuWater`; use
  `-ExecutePythonScript` in the full editor, not a Python commandlet.

## Retained original engine captures and measurements

- [Main hole before](images/2026-09-05-futaleufu-current-water/hole-before.png)
  / [final](images/2026-09-05-futaleufu-current-water/station-300.png).
- [Approach](images/2026-09-05-futaleufu-current-water/station-24.png),
  [entry](images/2026-09-05-futaleufu-current-water/station-150.png), and
  [recovery](images/2026-09-05-futaleufu-current-water/station-480.png).
- [Entry opposite side](images/2026-09-05-futaleufu-current-water/side-180.png)
  / [second-hole opposite side](images/2026-09-05-futaleufu-current-water/side-320.png).
- [First main-hole frame](images/2026-09-05-futaleufu-current-water/hole-first.png)
  / [later frame](images/2026-09-05-futaleufu-current-water/hole-later.png).
- [Rejected square-grid ripple](images/2026-09-05-futaleufu-current-water/rejected-square-grid.png),
  [flat mesh-normal diagnostic](images/2026-09-05-futaleufu-current-water/bisect-flat-mesh-normals.png),
  [disabled material-normal diagnostic](images/2026-09-05-futaleufu-current-water/bisect-no-material-normal.png).
- [Baseline timing](images/2026-09-05-futaleufu-current-water/performance-before.json),
  [final timing](images/2026-09-05-futaleufu-current-water/performance-after.json),
  [material audit](images/2026-09-05-futaleufu-current-water/material-audit.json),
  [Python results](images/2026-09-05-futaleufu-current-water/python-checks.json).

Full sequences remain in `unreal/Saved/Screenshots/futaleufu_final_*` and
`futaleufu_side_*`. No generated image stands in for engine output.
