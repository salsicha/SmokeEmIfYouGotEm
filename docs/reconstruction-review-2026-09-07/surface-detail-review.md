# Actual crux captures and ripple isolation — 2026-09-07

Status: useful rendering diagnosis and two isolated shader candidates, **not
South Fork completion or production acceptance**. The captured terrain,
one-metre hydraulic package, native solver archive and saved map are unchanged.

## What the camera was missing

The old guided test requested images every 30 seconds. In the previous
`SouthForkGuidedTraversal_20260907_175108.json` run, its first request was around
station -55 m, the next at +39.62 m and the next at +105.34 m. It skipped the
crux around local station zero. The smooth runout pictures were not evidence
that the whole rapid had no displacement.

`-RaftSimSurveyStationCaptures` now requests the initial view, each 15 m station
from -45 m downstream, and the outlet. Each request records filename, elapsed
simulation time, station and lateral position in the traversal JSON. These are
**request** positions, not a claim of exact render-thread exposure coordinates;
actual files must also be checked. No navigation thresholds were relaxed.

The station-zero captures show raised water and froth, but rounded/sheet-like
foam, overly smooth faces and stepped shore corners remain. This is the gray
captured-geometry diagnostic map, not the dressed production scene.

## Runtime material, not the production parent

The visible carrier uses
`M_RaftSim_LiveRiverSurface_SurfaceLitReview`, a surface-lit translucent
derivative of `M_RaftSim_LiveRiverSurface`. It does **not** use the production
South Fork Single Layer Water parent. Tuning only that other parent's
`FlowRippleStrength` would not fix this review's `LiveRippleStrength` output.

`SouthForkGuidedTraversal_20260907_182826.json` records the bound material,
1.5 m presentation vertex spacing and its texture parameters. All four
`LiveWaterFlowNormalPrimaryA/B` and `LiveWaterFlowNormalCrossA/B` bindings point
to the South Fork 1254-square generated normal. The texture has **11 platform
mips and wrap addressing**. The missing-mipmap hypothesis is therefore rejected.
The source PNG/provenance describes the older mirrored-image workflow; it is
not authoritative evidence of today's GPU sampler state.

Another code mismatch remains: runtime river-specific normal selection writes
the legacy `LiveWaterFlowNormalPrimary/Cross` names, whereas the current graph
uses the A/B names. This does not establish that the current South Fork run
had a non-null alternative texture configured, but needs a binding regression
when correcting the reusable carrier path. Parameter enumeration includes
unused graph branches; it is not proof every enumerated texture is sampled
by the final pixel shader.

## Controlled visual comparisons

Every listed raw report is in `unreal/Saved/Automation`; its numbered images
are in `unreal/Saved/Screenshots`. The durable aggregate `guided-review.json`
retains all 22 historical runs, including failures.

| Variant | Raw report suffix | Route error, m | Engine result |
| --- | --- | ---: | --- |
| Station-capture baseline | `20260907_181656` | 4.40 | Pass |
| Micro-normal disabled only | `20260907_182027` | 4.93 | Pass |
| Runtime texture audit | `20260907_182826` | 4.74 | Pass |
| Aperiodic normal V1 | `20260907_184024` | 4.85 | Pass |
| Finer aperiodic normal V2 | `20260907_184921` | 5.10 | **Fail** |

The prefix is `SouthForkGuidedTraversal_`; files end in `.json`. The threshold
is still 5 m. V2 reached the outlet in 66.83 seconds with minimum sampled tube
clearance 29.89 cm, but this does not cancel its route-error failure. Different
wall-frame schedules and capture costs can expose the existing guide's lack
of robustness; do not infer a physics change from a shading-only A/B, or repeat
until one lucky pass hides this failure.

Actually viewed each normal variant's `_003` and `_004` frames, near stations
-15 and zero. Disabling `LiveRippleStrength` removes the fine parallel texture
but leaves the broad water/foam shapes unchanged. It is a diagnosis, not a
solution of removing all ripple detail.

V1 replaces the sampled normal with three current-carried, rotated quintic
value-noise gradients. It removes the fine texture but reads as broad bands
from the raft. **Do not promote V1.**

V2 uses smaller compact gradient kernels on a triangular lattice with analytic
derivatives and footprint filtering. It avoids V1's square-grid zero-gradient
lines and has less conspicuous fine streaking in these views. It still does
not make the scene photographic. Both use the existing integrated-current
coordinate, no independent panner or elapsed-time phase, and change only the
normal output: **neither adds geometry, simulates fluid, nor changes support**.

Sources are `unreal/Shaders/Private/RaftSimCurrentSurfaceNormal.hlsl`,
`unreal/Shaders/Private/RaftSimCurrentSurfaceNormalV2.hlsl` and
`unreal/Scripts/create_survey_current_normal_review.py`. The creation script
refuses an existing destination, duplicates the review material, verifies
unchanged map/source hashes and compiles the shader. Setup reports retain the
source-code hashes. These are first-party code-native mathematical shaders;
no remote bitmap was copied or generated.

Runtime opt-in is `-RaftSimSurveyBreakingReview` plus either
`-RaftSimSurveyCurrentNormalReview` or `-RaftSimSurveyCurrentNormalV2Review`.
The latter takes precedence. The normal carrier initialization still applies
all normal live parameters. The test verifies the requested material binding.
Defaults and the saved map remain unchanged. Unreal builds and both material
compiles succeeded; no shader-compile error was found in those creation logs.

## Fixed-bank sequence and cost

`SurveyCurrentNormalV2Bank_000.png` through `_023.png` are a 24-frame,
0.10-second requested-interval sequence after 10 simulation seconds. Command:

`RaftSim.CaptureSeries 10 24 0.10 SurveyCurrentNormalV2Bank river_station_side focusstation=0 focuslateral=0`

Only the camera moves to the fixed focus; no station-walk or raft teleport is
requested. Log resolves surface 7.407 world metres and camera approximately
(451.93, 735.37, 1090.66) world cm. All 24 files exist. Frames 0, 12 and 23 were
viewed individually: spray/foam/detail change, but smooth broad white shapes
and a stepped near-bank boundary remain. This is **not continuous playback,
motion-flow calibration, or temporal acceptance**. The game-mode startup logs
also contain the existing toolset Python `PythonTestRunner` import error;
successful captures do not resolve that maintenance issue.

Two clean, non-concurrent offscreen game soaks use 1280x720 output, 87% internal
screen percentage, the active RTX 3060 Laptop GPU, 5-second warmup and 20-second
sample duration. These are not packaged-release qualification.

| Variant | Mean frame ms | p95 frame ms | Mean solver ms | Mean GPU ms |
| --- | ---: | ---: | ---: | ---: |
| Original texture normal | 13.930 | 19.090 | 8.961 | 6.493 |
| V2 procedural normal | 13.791 | 18.988 | 8.912 | 6.478 |

The small difference is within run variation, not evidence of a speedup. Both
fail the 16.667 ms p95-frame and 1.6 ms solver budgets. Reports:
`survey_performance_current_normal_baseline.json` and
`survey_performance_current_normal_v2.json`. No quality cuts, frozen flow,
coarser hydraulic grid, or hidden crew were used to obtain these results.

## Remaining direction

Stop trying to solve the missing large breaking-water shape with normals.
Investigate the actual carrier's shoreline clipping and 1.5 m mesh/3 m analysis
sampling; connect resolved drop/obstacle controls to crest/roller geometry and
advected foam. Profile the settled native workload, not another cold offline
compiler experiment. Register the captured rock controls against the viewed
references before making unsupported bathymetry/layout claims. Stateful local
GPU fluid, route robustness, full-route promotion and all later queued rivers
remain open. The goal and final-commit requirement remain active.
