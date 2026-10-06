# Chili Bar to Salmon Falls water review — 5 September 2026

Status: a verified rendering-maintenance pass, **not realistic-whitewater acceptance**. Remaining broad highlights and insufficient breaking-wave volume are visible in the captures below.

## Changes

- Rebuilt 39 authored river-water tiles (13 tiles across three runnable flow bands) and the Salmon Falls continuation with full-precision UV buffers. All 40 previously used half precision. At 48 km, adjacent 1.5 m rows collapse to the same float16 station coordinate; float32 preserves them. Future water-mesh authoring now applies the same setting, without changing foliage meshes or collision.
- Matched the static water instance to the live carrier's finer normal detail, torn foam contrast and matte foam roughness. Disabled the old independent turbulence displacement on the static instance. This avoids divergent presentation settings between authored and live surfaces; it does not introduce another layer.
- Migrated the actual saved V4 parent's analytic-normal branch. It lacked the `AnalyticChopStrength` parameter that runtime code had been setting to zero, so that setting previously did nothing. The new gate is wired into the old crossing-sine slope branch and defaults to zero.
- Material graph refresh now generates a new `StateId` and updates cached expression data before saving. Unreal requires a new material identity for expression changes that are not independently part of the shader-cache key. This prevents a newly saved graph from relying on a stale key; it does not prove that every earlier artifact came from stale shaders.
- Added a shallow-depth envelope to the existing GPU boil displacement: zero below 10 cm, smoothly reaching full strength at 60 cm. It uses the carrier's green vertex channel, encoded as depth divided by four metres, and retains the existing wetness and distance gates. This limits render-only shore boils; it does not repair all terrain/water intersections.
- Added a map-scoped, command-line-only review start and a sequential four-location capture script. Review runs ignore checkpoint location without changing the player's saved selection. Ordinary runs remain unchanged.

No extra solver cells, mesh vertices, water surfaces or particle systems were added. Hydraulic data, flow, buoyancy and collisions were not changed in this pass.

## Actual gameplay evidence

The full map is `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`. Each accepted capture log verifies its requested start station. These are engine backbuffer captures, not generated reference art.

| Section | Start station | Capture |
| --- | ---: | --- |
| Upper reach | 120 m | [Upper](images/2026-09-05-southfork-full-reach-water/upper.png) |
| Coloma | 12,000 m | [Coloma](images/2026-09-05-southfork-full-reach-water/coloma.png) |
| Gorge near Satan's Cesspool | 27,170 m | [Gorge](images/2026-09-05-southfork-full-reach-water/gorge.png), [later frame](images/2026-09-05-southfork-full-reach-water/gorge-later.png) |
| Salmon Falls end | 48,000 m | [Lower reach](images/2026-09-05-southfork-full-reach-water/salmon-falls.png) |

Each final location has an eight-frame burst at requested 0.25 s intervals. Representative frames and separated gorge frames were visually inspected. This is not a continuous-video flicker qualification or a complete 49 km traversal. The initial `upper_before`/`lower_before` captures were rejected: the first version of the review override was overwritten by scenario configuration, leaving both at Troublemaker. The override was moved to session configuration and subsequent logs verify the correct stations.

A temporary zero-foam capture at Coloma retained broad highlights. A separate zero-normal-strength capture also retained those highlights while losing fine ripples. Consequently, neither the new normal gate nor the UV repair is claimed to eliminate that entire remaining pattern. Further isolation of the base surface/reflection contribution is needed, without flattening genuine hydraulic crests.

## Validation and performance

- Development Editor build passed after the final C++ changes.
- Twelve focused source/numeric regression tests passed, invoked directly with Python because pytest is not installed. These are five full-reach presentation guards and seven existing performance/banding guards, not the complete gameplay suite.
- Saved material audit passed: one shared UV origin, 14 rebased coordinate readers without bypasses, a connected zero-default analytic-normal gate, and bounded boil phase.
- A fresh editor process reopened all 40 water meshes and confirmed full-precision UVs on every asset: [saved tile audit](images/2026-09-05-southfork-full-reach-water/tile-audit.json).
- The tile audit requires `-ExecutePythonScript`, not `-run=pythonscript`, because the commandlet does not instantiate `StaticMeshEditorSubsystem`.
- Existing historical shared-foam source-token/hash tests remain outside the passing set; historical evidence was not rewritten to manufacture passing results.

The [performance sample](images/2026-09-05-southfork-full-reach-water/performance.json) measured 20 seconds after 12 seconds of warmup at the gorge start, with no screenshots during measurement: 1,621 frames, 1280×720 output, 87% screen percentage, medium scalability, Development/offscreen on a Ryzen 7 5800H / reported AMD Radeon Graphics.

| Measurement | Result |
| --- | ---: |
| Mean wall frame | 12.35 ms, approximately 81 FPS |
| P95 wall frame | 27.84 ms |
| Maximum wall frame | 37.50 ms |
| P95 game thread | 25.86 ms |
| P95 GPU | 8.45 ms |
| Average solver step | 0.258 ms |
| Frames over 33 ms | 3 |

Solver and memory budgets passed; the 60 FPS frame budget failed. This is not packaged/focused-window release qualification, nor evidence of an improvement over Troublemaker's earlier measurement: they are different hydraulic windows. No active rapid roller/aerosol emitters were recorded in this gorge sample, so it is not a worst-case breaking-water benchmark.

## Reproduction and remaining work

Run `unreal/Scripts/review_south_fork_water.ps1` for sequential upper/Coloma/gorge/lower captures. Override `-Stations` and `-Label` as needed. The game flag is `-RaftSimWaterReviewStation=<metres>`; it is restricted to this map and 0–48,900 m.

Run `unreal/Scripts/audit_south_fork_water_tiles.py` through Unreal's `-ExecutePythonScript` for a read-only inventory. `-RaftSimRepairWaterTiles` explicitly enables repairs. Refresh the saved material with `-ExecCmds="RaftSim.RefreshSolverCurrentFoamMaterial Quit"`; `Quit` here is the refresh command's argument.

The river still needs better large-scale rapid shape, resolved curling/breaking crests, aerated rollers, and shoreline geometry. Broad pale highlights remain particularly visible in calm stretches. The current bounded shader is an analytic heightfield, not a volumetric fluid simulation. Do not present these changes as completing the user's realism objective.
