# Grand Canyon / Hance water — 5 September 2026

Status: improved current detail, restored visible aeration and reduced surface-update cost. **Not photoreal or sustained-60-FPS acceptance.** This reviews the shipped `/Game/RaftSim/Maps/L_Hance` scene, an interpreted 600 m window, not the entire Grand Canyon.

## Changes and evidence

The baseline runout had fine photographic ripples beneath broad pale bands, with almost no discernible white froth. An unlit isolation capture removed the bright bands, placing them in the lighting/normal response rather than the base foam color alone. The river's existing normal source also has strong diagonal ridges; the historical September 2 review documented its mirrored-tile artifacts.

Hance now has a separate `M_RaftSim_ColoradoCurrentWaterV3` parent, cloned from the existing transmitting-water parent so the raft aperture, optical depth, shared foam advection and local boil displacement remain intact. Only Colorado's live material instance is reparented; other rivers retain their materials.

The new normal branch uses two rotated, non-periodic hash-gradient fields at different scales, advected by the same integrated current displacement as foam. It evaluates continuous analytic derivatives, reconstructs river coordinates from the existing UV origin and fades subpixel detail using the pixel footprint. It has no periodic time-driven sine lanes or photographic normal repeats. It is optical surface detail, **not** a new fluid solver or additional geometry layer. Old texture parameters remain as compatibility metadata but no longer drive this normal output.

A separate confirmed defect hid Hance's aeration: the inherited material subtracted 0.28 before showing foam, while the initial runtime inventory peaked near 0.261. At 0.9 intensity this was discarded entirely. The Colorado copy now uses a 0.04 onset, coverage gain 4.0 and core gain 1.8. Speed-only whitening is disabled. Existing aeration, current-advection and torn-lace masks still determine coverage; the change does not seed foam into zero-aeration water. The new captures show visible broken foam on the drop/runout and a mostly foam-free pool.

The Hance render lattice is capped at one metre instead of half a metre: 23,377 vertices / 46,080 triangles rather than 92,833 / 184,320. The initial logged surface refresh fell from 95.49 ms to 22.53 ms. This is a single-update diagnostic comparison, not a controlled end-to-end FPS speedup measurement. The underlying hydraulic grid is unchanged. The coarser presentation grid retains metre-scale crests but does not resolve overturning lips or small splashes geometrically.

## Actual gameplay captures

- [Before, runout](images/2026-09-05-colorado-current-water/before.png)
- [Updated runout](images/2026-09-05-colorado-current-water/runout.png), [later animation frame](images/2026-09-05-colorado-current-water/runout-later.png)
- [Calm pool, start station 100 m](images/2026-09-05-colorado-current-water/pool.png)
- [Main-drop approach, start station 300 m](images/2026-09-05-colorado-current-water/drop.png)

These are 1280×720 game backbuffer captures. The runout starts at 410 m; the raft then drifts, so numbered before/after images are not guaranteed to have identical positions. The final runout has 12 frames at requested 0.3 s intervals; pool and drop have eight each. Representative and separated animation frames were inspected. This is not a continuous-video flicker qualification, a complete traversal or a measured match to real Hance footage.

`unreal/Scripts/review_hance_water.ps1` reproduces the three positions sequentially and checks arrival, output images and material-compile failures. It uses a raft-following three-quarter camera, without adding rocks or staging new hydraulic features.

## Validation

- Development Editor build passed after all C++ changes.
- `RaftSim.M9.FColoradoHanceWater` passed in Unreal, including the new live-parent reference and existing transmitting-water/texture checks.
- The automation prefix also selected `FColoradoHanceWaterCapture`; that test failed because it was run with NullRHI, where its saved-camera pixel readback is unavailable. This is reported as a failed test, not counted as passing. The separate gameplay captures above used actual rendering and succeeded.
- Sixteen focused source/numeric guards passed by direct invocation with the bundled Python (pytest is unavailable): four new Colorado guards, seven existing performance/banding guards and five full-reach material guards. The new checks cover advection/UV reconstruction, derivative filtering, the foam cutoff, the Hance-only lattice cap and analytical noise derivatives versus finite differences.
- [Saved material audit](images/2026-09-05-colorado-current-water/material-audit.json) passed against the actual Colorado instance, custom normal and foam cutoff. No HLSL material-compilation failure appeared in the gameplay capture logs.
- No full gameplay regression suite, packaged-release test or new hydraulic-data cook was performed. Boat forces and collision code were not changed, but the lower render-update load changes simulation cadence, so this is not proof of trajectory equivalence.

## Performance

[Raw sample](images/2026-09-05-colorado-current-water/performance.json): 20 seconds measured after 12 seconds warmup, normal Hance launch, no screenshots during measurement, 1,392 frames. Development/offscreen, 1280×720 output at the saved 87% screen percentage, medium scalability, Ryzen 7 5800H / reported AMD Radeon Graphics. Four rapid roller and four aerosol emitters were active at report time.

| Metric | Result |
| --- | ---: |
| Mean wall frame | 14.38 ms, approximately 69.6 FPS |
| P95 wall frame | 32.61 ms |
| Maximum wall frame | 35.82 ms |
| P95 game thread | 32.34 ms |
| P95 GPU | 7.82 ms |
| Average solver step | 2.86 ms |
| Frames over 33 ms | 41 |

The frame and solver budgets **failed**; memory passed. This offscreen engineering sample is not a focused packaged-build qualification. The remaining bottleneck is principally game-thread work, not the new shader's measured GPU time.

## Remaining limitations

Large breaking rollers still lack convincing overturning crests, dense aerated volume and spray integration. Broad smooth highlights remain in the pool, although the normal pattern and rapid foam are more varied. The interpreted terrain has angular terraces and insufficient Grand Canyon geology. Occasional render/raft freeboard mismatch is still present in telemetry; this pass did not replace the support field. The new shader does not fix those geometric or hydraulic limitations, and the result should not be described as a finished realistic Hance simulation.

To refresh/audit the authored water, use `-ExecutePythonScript=.../unreal/Scripts/review_colorado_water_assets.py`; add `-RaftSimRefreshColoradoWater` only when intentionally rebuilding the Colorado water materials/textures. Without that flag the script is read-only apart from its validation JSON.
