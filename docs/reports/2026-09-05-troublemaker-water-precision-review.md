# Troublemaker water review — 5 September 2026

Status: rendering defects improved; **not photoreal acceptance**, and the 60 FPS performance gate still fails.

## Verified cause and changes

The actual player scene is `L_SouthForkAmerican_FullReach`, using the Troublemaker cooked hydraulic window and `M_RaftSim_SouthForkRaftTransmissionWaterV4`. This review did not substitute the legacy Troublemaker map or add staged obstacles.

The main procedural carrier uploaded absolute station/3 texture coordinates into Unreal's default half-precision procedural-mesh UV buffer. Around station 8352 m, adjacent 1.5 m rows collapsed onto the same representable UV value. Texture interpolation then stretched the foam into long streaks separated by transverse bars. Flat-normal and unlit diagnostic captures retained the pattern; disabling hydraulic foam removed it.

The carrier now uploads local river coordinates. A shared material uniform restores the absolute river phase after interpolation. Its origin changes in 384 m increments; all 14 UV0 readers in the saved parent reconstruct that origin, including their individual tiling scales. UV1 flow data is untouched. Static tiles retain their original coordinates with a zero default origin. Unmigrated materials retain the previous behavior rather than receiving incompatible coordinates.

The corrected coordinates allow restrained, aeration-weighted fine normals to be restored. Foam now has lower uniform coverage, stronger torn-lace contrast, and higher roughness. No extra surface, vertices, particles, or solver cells were added. Current advection, hydraulic sampling, buoyancy, and collision are unchanged.

The local boil shader also no longer multiplies advected noise by elapsed time. Its phase offsets are bounded, preventing session age from progressively increasing the noise's temporal derivative. This is an analytic presentation field, not a new volumetric fluid simulation.

## Evidence

- [Before: collapsed foam UVs](images/2026-09-05-troublemaker-water/before.png)
- [After: corrected coordinates and detail](images/2026-09-05-troublemaker-water/after.png)
- [After: later animation sample](images/2026-09-05-troublemaker-water/after-later.png)

Actual offscreen gameplay bursts were inspected from the chase camera, a drifting offset camera, and the hydraulic-site side view. The final same-camera burst contains 24 frames at requested 0.2 s intervals. Drifting-camera evidence contains 32 frames at requested 0.15 s intervals. These are screenshot bursts, not a frame-rate benchmark or a full continuous-video flicker qualification.

Reproduce the final burst with UnrealEditor-Cmd, the project, the full-reach map, and:

```
-game -Unattended -NoSplash -RenderOffscreen -ResX=1280 -ResY=720 -windowed
-ExecCmds="RaftSim.CaptureRaftSeries 8 24 0.2 troublemaker_water_final 5 0 1.4 14 station=8352"
```

## Validation

- Development Editor build passed.
- `RaftSim.P2.WaterTexturePrecision` passed: half-precision round trip at 0, 8352, and 48900 m; 401 rows per station; identical reconstructed phase across an origin change; reproduction of the old row collapse.
- `unreal/Scripts/audit_troublemaker_water.py` passed against the saved asset: one shared origin, 14 wrapped UV0 inputs without bypasses, bounded boil phase. Repeated material refresh did not duplicate wrappers.
- Ten of thirteen standalone source guards passed, including all seven performance/banding guards. Pytest is unavailable in the bundled Python, so the ordinary zero-argument test functions were invoked directly. Three older shared-foam guards still fail: retired wet-mask source tokens, old shoreline implementation tokens, and historical source hashes. Those historical evidence records were not rewritten to manufacture a passing result.
- No full gameplay automation suite or packaged release validation was run.

## Performance sample

20 seconds measured after 12 seconds warmup, no screenshots during measurement, actual Troublemaker window; 811 frames. Development/offscreen, 1280×720 output at the saved 87% screen percentage, medium scalability, Ryzen 7 5800H / reported AMD Radeon Graphics.

| Measurement | Result |
| --- | ---: |
| Mean wall frame | 24.67 ms (about 40.5 FPS) |
| P95 wall frame | 41.34 ms (about 24.2 FPS equivalent) |
| Maximum wall frame | 44.67 ms |
| P95 game thread | 41.38 ms |
| P95 render thread | 14.73 ms |
| P95 GPU | 10.75 ms |
| Mean solver step | 10.26 ms |
| Frames over 33 ms | 275 |

The 16.67 ms frame and 1.6 ms solver budgets **failed**. This is not a packaged, focused-window performance qualification, and there was no matched before/after performance run establishing a speedup. The game thread is the dominant measured bottleneck.

## Remaining visible limitations

The shoreline still has coarse angular sections and raised water near banks. The main rapid's large-scale hydraulic shape and dense breaking roller remain substantially less convincing than real Troublemaker. Fine shading cannot replace missing resolved crest geometry or terrain/hydraulic alignment. The same-camera test raft also rests on a boulder, so it is not evidence of successfully navigating the rapid; the separate offset burst checks drifting presentation.

Do not label this work a complete realistic-whitewater implementation. It fixes a confirmed precision defect, restores usable surface detail, and removes a mathematically unstable animation term while preserving the existing one-carrier design.

## Goal follow-up: weak hydraulic control, not only weak shading

Fresh baseline: `troublemaker_goal_baseline_000..011.png`, actual full-reach
map and Troublemaker median cooked window. Inspected frame 003. A four-station
survey at 8358/8374/8390/8406 m produced chase, later chase and side images;
inspected 8374 m side view. The surface remains broad, pale and smooth, with
raised angular bank sections and no convincing retained breaking roller. The
8352 m capture raft is on a boulder; this does not prove a successful run.

Reopened the user's [John Elkins Troublemaker footage](https://www.youtube.com/watch?v=ZEG1kvjNI30)
through the in-app browser because the web text fetch failed. Inspected paused
frames at displayed 10, 20, 35 and 40 seconds. At 35–40 seconds the dark steep
faces, bright irregular crests and compact rock-confined roller differ greatly
from the game. These sampled frames do not constitute full-motion or measured
wave-height calibration. No third-party media was downloaded. The requested
hole/right-turn/left-turn sequence remains the scene target, not a surveyed map.

The visible live mesh contains legitimate aeration data: 7,000 wet vertices,
1,104 with R > 0.2 and 154 with R > 0.5 at the delayed baseline probe. It uses
the saved V4 parent, not the hidden SurfaceMesh. However the hydraulic field
itself is weak at the intended control. Direct measurements of the saved
median arrays inside lateral ±15 m and depth >0.1 m:

| Station interval | Median speed | Median / p90 / p99 Froude |
| --- | ---: | --- |
| 8340–8360 m | 1.132 m/s | 0.460 / 0.818 / 1.326 |
| 8360–8380 m | 0.652 m/s | 0.203 / 0.435 / 0.668 |
| 8380–8410 m | 1.386 m/s | 0.420 / 0.686 / 0.852 |
| 8410–8440 m | 0.944 m/s | 0.239 / 0.369 / 0.505 |

The live survey agrees that the hole region is mostly slow: 8374 m centerline
water speed 0.71 m/s, depth 1.31 m. The terrain trace returned no hit there;
do not interpret its zero clearance as verified terrain alignment.

The generator cooks only 480 × 0.02 s = 9.6 requested seconds. Its committed
median evaluation reports entry 61.27, rapid section 16.39 and outlet 274.84
m³/s against a 45.31 m³/s target. Those unequal sections are evidence of a
transient, not a settled discharge. Existing broad validation tolerances did
not establish a physically convincing hole.

Added `physics/scripts/audit_troublemaker_hydraulic_spinup.py` to run the same
scenario/configuration longer into a separate output directory and compare
wet-cell speed/Froude/stage, section discharge and total volume snapshots. A
synthetic unit check verifies flux units and dry-cell exclusion. The 96-second
requested diagnostic was launched in `tmp/troublemaker-spinup-goal`, using
`tmp/troublemaker-solver-ninja/raftsim_water_solver.exe`; no shipped arrays or
materials were replaced. At this update the process is still running (tool
session 34482, solver PID 35416). Inspect that live handle/results before any
retry. Its results, not elapsed waiting time, determine whether a longer cook
or a revised interpreted channel control is the next implementation step.

### Longer-cook result and isolated throat experiment

The existing executable was a Debug build. Built a separate Release executable
from the current C++ source in `tmp/troublemaker-solver-release`; its standalone
transcritical-bump checks passed (determinism, well-balanced behavior, state
replacement, coupling and output). This is not a validation of the Troublemaker
scene. Initial configure attempts needed explicit Ninja/compiler/SDK paths;
the completed build did not replace the engine library or the running binary.

The Release 96-second baseline completed in 410.10 wall seconds. Its 9.6-second
snapshot closely reproduces the shipped hole statistics (median speed 0.651
versus 0.652 m/s). By 96 seconds the hole's median speed reaches 1.260 m/s, but
median/p90/p99 Froude remains 0.347/0.626/0.807, with only about 0.1% of wet
cells supercritical in the 8360–8380 m, lateral ±15 m region. Median statistics
alone do not prove absence of a narrow jet; inspect spatial fields as well.

At the 96-second snapshot, section discharges are 54.46 m³/s at 8180 m,
35.91 at 8348 m, 34.52 at 8362 m, 32.56 at 8378 m, 30.95 at 8400 m,
29.26 at 8440 m and 9.76 at 8550 m. Total water volume is still changing:
20,163.7 m³ at 86.4 seconds and 20,650.8 m³ at 96 seconds. The generic solver
validation says passed, but this is **not settled-flow acceptance**. Longer
spin-up improves the early transient yet has not established a strong main
hole. No baseline fields were promoted. The redundant original Debug solve
was deliberately stopped after this complete optimized result; its session
ended with the expected termination error, not a numerical failure.

Added an optional `--throat-width` experiment to the diagnostic. A 12 m authored
control raises submerged shoulders over station −34 to +12 m relative to the
rapid, follows the existing interpreted S-shaped thalweg, and retains the
central sill/drop. This width is an authoring hypothesis based on the compact
rock confinement in the reference, not a measurement or surveyed geometry.
Dry terrain is unchanged; the bank transition is feathered. Reinitialized
column velocities preserve original section flux, rather than introducing
runtime velocity forcing. Tests verify locality, source-array immutability,
nonnegative bed raising, flux preservation and invalid-width rejection.

The candidate is stored only under `tmp/troublemaker-throat12-spinup`, carries
`production_promoted=false`, and has not changed gameplay. Its 96-second
Release solve completed in 401.23 wall seconds. It is **not promoted**:
discharge at the same seven sections above fell to 50.02, 26.02, 24.82,
23.15, 21.48, 20.79 and 0.55 m³/s. The stronger local jet does not compensate
for reduced conveyance and the worsened downstream imbalance. Evidence:
`images/2026-09-05-troublemaker-water/hydraulic-spinup-throat12-96s.json`.

Spatial inspection corrects an overly broad reading of the regional medians:
the longer baseline *does* contain a narrow supercritical jet. At station
8358 m within lateral ±3 m its median speed/depth/Froude are
3.017 m/s / 0.634 m / 1.225. At 8362 m they become
1.754 m/s / 1.275 m / 0.496, with a 0.160 m median surface recovery.
The narrower-throat candidate reaches 3.241 m/s / 0.692 m / 1.252 upstream,
but remains 2.231 m/s / 1.134 m / 0.669 downstream without that surface
recovery. In the 8340–8390 m, lateral ±15 m region, supercritical cells carry
4.17% of the baseline's positive downstream flux versus 10.12% for the
candidate. These are diagnostic snapshots, not steady-flow acceptance or
evidence that the current game renders either 96-second field.

Next ablation: the current visible carrier applies sixteen smoothing passes
at a 3 m analysis stride. This predates the half-precision UV repair and can
erase feature-scale surface curvature. Added a South Fork-only optical-pass
review control, defaulting to the existing sixteen. The hydraulic source
keeps its separate four-pass filter, including when the optical comparison
uses fewer passes; wet-neighbor and shoreline guards remain unchanged.

### Optical smoothing A/B — not promoted

Built and captured separate fresh game sessions at station 8358 m with
`raftsim.SouthForkOpticalSmoothingPasses` set to 16 and 2. Each produced twelve
1280×720 frames using `RaftSim.CaptureRaftSeries 8 12 0.2 <label> 5 0 1.4 14
station=8358`. Logs verify the active values and the fixed four hydraulic
passes. The second run initially builds with the default, then applies the
override at frame 1 before the capture. These are separate live runs, not
synchronized deterministic replays. Screenshot readbacks perturb timing.

Inspected frame 003 from both sessions and frame 011 from the two-pass run.
Both show broad, smooth pale water, weak surface relief, and the unresolved
raised green bank shape. Neither resembles the steep dark faces and breaking
white roller in the user's reference at 35–40 seconds. The reduced filter does
not establish a convincing hole or continuous foam. Keep the default sixteen;
the new control is diagnostic, not a claimed realism improvement.

![Sixteen-pass baseline](images/2026-09-05-troublemaker-water/troublemaker_optical16_003.png)

![Two-pass comparison](images/2026-09-05-troublemaker-water/troublemaker_optical02_003.png)

`RaftSim.P2.WaterSmoothingScale` passed in the engine. Using the actual helper
on an 18 m test wavelength, 1.5 m sample spacing and 3 m analysis neighbors,
two passes preserve 56.25% of amplitude; sixteen preserve 1.002%. This confirms
attenuation, not the cause of every visual defect. A separate NumPy sampling
of the shipped 0.5 m field at 1.5 m intervals, using the same kernel and a wet
neighbor guard, measures grade-removed centerline extrema over 8340–8380 m:
raw −0.421/+0.025 m, two-pass −0.254/+0.008 m, four-pass −0.212/+0.003 m,
sixteen-pass −0.108/+0.0005 m. That is a static cooked-field approximation,
not an export of live rendered geometry. The input mainly contains a trough,
not a large positive breaking crest.

Fresh isolated 20-second performance soaks, after 12 seconds warmup, used
the same map, 8358 m review start and 1280×720 offscreen window, with no
screenshot readbacks or concurrent solver/build:

| Optical passes | Frames | Mean wall frame | p95 wall frame | Mean solver step |
| --- | ---: | ---: | ---: | ---: |
| 16 | 701 | 28.533 ms | 44.012 ms | 10.062 ms |
| 2 | 702 | 28.545 ms | 43.440 ms | 10.616 ms |

Both fail the frame and solver budgets. A single A/B pair shows no meaningful
average improvement; it is not release-performance qualification. Preserve
`performance-optical16.json`, `performance-optical02.json` and matching logs.
Thirty-nine plain Python presentation/diagnostic checks also passed; both
editor builds succeeded. These checks do not qualify photorealism.

Next: establish a better settled hydraulic input before more optical tuning.
The 96-second baseline has a narrow jet but still-changing volume and unequal
section discharges. Check a longer baseline (or a reproducible warm-start from
that result) for convergence before adjusting control geometry again. Do not
promote the short-cook narrowed throat just because its jet is stronger.
Troublemaker remains open; animation and shoreline realism remain unaccepted.

### Warm-start continuation and isolated field preview

Extended the hydraulic diagnostic with a validated CSV warm start. It checks
complete unique integer indices, matching coordinates/bed, finite nonnegative
depth, momentum consistency and the wet mask before constructing initial
fields. It preserves the source arrays and records the frame SHA-256 and
elapsed time. This restarts the solver clock, so it is not a bitwise checkpoint;
this diagnostic has constant boundaries and disabled feature forcing.

The 96-second baseline source passed these checks, preserving 20,650.8023 m³
of water and its momentum fields. Source SHA-256:
`2fcd97d72a2189cda7d7b4b9cddb5e31ddb1ad3390f9b8dc66f13cd46ef9276a`.
Launched another 192 seconds into `tmp/troublemaker-spinup-warm288`, for
288 nominal cumulative seconds. At this update session **10048**, solver
PID **37068**, is confirmed active. The solver accumulates frames in memory
and writes them after `run()` completes; the missing output directory is not
evidence of termination. Resume this handle, not a duplicate solve.

Added `physics/scripts/export_troublemaker_review_fields.py` to turn a
validated baseline frame into an explicitly unaccepted median-only review
package under a *new* repository `tmp` directory. It applies the existing
shock limiter, hashes the arrays, retains the original grid/datum/boundaries
and runtime solver settings, and removes stale production steps/binary-hash
claims. The package is labelled `production_promoted=false` and
`all_bands_passed=false`; these are review artifacts, not replacement data.
The 96-second package at `tmp/troublemaker-review96` passed manual checks of
grid/datum, runtime settings, boundaries, array shapes/dtypes and all hashes.
Its shock limiter changed zero cells. Initial inspection caught missing
runtime solver settings in the exporter; those were restored before any
game preview. No invalid package was loaded in-game.

Built a non-shipping, process-local
`-RaftSimTroublemakerReviewFields=<directory>` option in the river streamer.
It only overrides `south_fork_troublemaker_live_window`, requires the median
band and an existing manifest, and logs the diagnostic override explicitly.
Other windows and saved manifests remain untouched. The engine build passed;
four diagnostic tests passed, including restart mismatch rejection and the
scoped preview source guard. The actual candidate-load/game capture remains
pending until the standalone solve has stopped; do not run a performance
comparison concurrently with it.

### 288-second result, gameplay preview and long-run support-phase fix

Session 10048 completed normally. The additional 192-second solve took
1,178.03 wall seconds. At 288 cumulative seconds, the seven discharge sections
carry 43.00, 42.34, 42.45, 42.13, 41.98, 42.18 and 42.00 m³/s. This is much
more consistent than at 96 seconds, although still below the 45.31 m³/s
target. Volume changes from 22,023.08 to 22,040.77 m³ over the final 9.6 seconds
(0.080%); do not call it perfectly steady. The generic validation passes but
does not establish visual fidelity. Evidence: `hydraulic-spinup-warm288.json`.

Within lateral ±3 m, station 8358 has median speed 3.169 m/s, depth 0.713 m,
Froude 1.241 and stage −0.610 m. At 8362 these become 1.868 m/s, 1.433 m,
0.498 and −0.374 m: a 0.236 m surface recovery. That supports a modest
hydraulic jump, not the much stronger breaking roller seen in the reference.

Exported `tmp/troublemaker-review288` and ran three fresh game bursts: optical
16 passes, optical 2 passes, then 2 passes with temporary foam coverage gain
2.4 instead of 0.95. Logs prove the diagnostic field override, and the material
probe verifies gain 2.4 on the visible V4 carrier. All produced twelve frames.
Inspected frame 003 of each: stronger surface variation and patchy aeration,
but still rounded/smooth pale water rather than a convincing breaking hole.
Two passes and the foam gain are **not promoted**. The live source initially
detects eight accepted breaking sites; the delayed visible-core probe has
7,354 wet vertices, 1,590 with R>0.2 and 310 with R>0.5. The raft drifts at
1.67–1.73 m/s during the default burst, unlike the prior near-stationary
capture. This means attached-camera screenshots are not identical spatial
comparisons: movement during the eight-second capture delay can pass the
hole. Added a separate 8348/8360/8372 m survey for approach/side inspection.

![288-second diagnostic field, default optical filter](images/2026-09-05-troublemaker-water/troublemaker_cook288_optical16_003.png)

An isolated 20-second performance soak after 12 seconds warmup, at 8358 m
and 1280×720, measured 684 frames, mean wall frame 29.254 ms, p95 43.135 ms,
mean solver step 10.351 ms. Frame and solver budgets still fail. No offline
solver or build ran concurrently. This is not release-performance qualification.

Found and fixed a separate temporal defect in the shared CPU local-fluid
height helper used by raft support. It multiplied elapsed time by advected
noise, while the South Fork shader already used a repaired bounded phase.
The engine regression `RaftSim.P2.WaterBoilLongRunContinuity` reproduced
maximum vertical changes for just 1 cm of advection of 0.0653 m at 60 seconds,
0.4163 m at one hour and 0.4262 m at four hours. The test failed before the fix.
Now the clock rate is a constant 1.70, with additive bounded noise offsets
2.90×noiseB + 2π×noiseA, matching the material convention. The same test passes
at all four tested times; each sampled maximum is below 0.02 m. The broader
`RaftSim.P2.WaterSurfaceRenders` test and all 42 plain presentation/diagnostic
checks pass; builds succeeded. Before/after logs are preserved. This verifies
the helper's continuity, not hours of rendered gameplay or photorealism.

The narrowed-throat 96-second source also passes the new warm-start validator.
Its earlier discharge imbalance was transient; it should be compared at a
similar later simulation time before concluding whether it forms the needed
stronger hole. No narrowed-throat geometry or hydraulic arrays are promoted.

The 288-second field survey completed all three stations (nine images).
Inspected the 8348 m chase view and 8360 m side view: the input now makes
visible lobed relief and more aeration, but neither an attached breaking
white roller nor credible rock-confined whitewater. Detached spray and large
angular shoreline cuts remain obvious. Terrain traces miss at 8360/8372 m;
their reported zero clearance must not be treated as alignment verification.
The survey reports raft damage at two stations, so these shots are not a
successful navigation/collision acceptance run either.

![Approach, 288-second review field](images/2026-09-05-troublemaker-water/troublemaker_cook288_survey_000_08348m_chase.png)

![Side view, 288-second review field](images/2026-09-05-troublemaker-water/troublemaker_cook288_survey_001_08360m_side.png)

Started the matching narrowed-throat continuation in
`tmp/troublemaker-throat12-warm288`: 192 additional seconds from the validated
96-second throat frame, with `--throat-width 12`. The source frame hash is
`ce20e379caa207cc5a5225c59035e29a9dc89d4f0915b299b72ec1db2498b5eb`.
At this update session **58061**, solver PID **35864**, is confirmed live.
Resume this handle rather than starting a duplicate. Compare its later
discharge, surface rise and spatial Froude field with the completed baseline
before any visual trial. A changed-bed candidate also requires terrain
alignment; the existing baseline-only exporter deliberately rejects it.

### Terrain-query obstruction and spray-attachment checks

The narrowed-throat continuation has now completed (841.675 wall seconds).
At 288 simulated seconds, section discharges at 8180/8348/8362/8378/8400/
8440/8550 m are 32.79/31.85/32.17/32.03/31.88/31.99/29.89 m³/s,
well below the wider baseline's 42–43 m³/s. The central surface recovery is
only 0.034 m, versus 0.236 m in the baseline. Volume is still growing.
Generic validation passes, but this does not support promoting the narrowed
bed as a stronger, realistic hole. Evidence: `hydraulic-spinup-throat12-warm288.json`.
The finite-volume inlet uses a stage/velocity ghost state, not an enforced
discharge flux; investigate actual boundary flux before changing geometry
again. This is a hypothesis about the flow shortfall, not a proven solver bug.

Terrain diagnostics found a separate, concrete runtime fault. Hidden
`SM_south_fork_02_WhitewaterFoam_high_runnable` blocked the centreline trace
above visible, collidable terrain. Direct terrain-component traces succeeded.
A bounded four-ray filter alone still missed; hiding a mesh does not disable
its collision. The streamer now disables actor collision on specifically
tagged water/foam presentation carriers, including newly streamed cells.
Terrain, boulders and raft collision are not selected by this change.

The same 8348/8360/8372 m survey now reports **three terrain hits instead of
zero**, with terrain elevations 19921/19962/19942 cm and water clearances
198/117/136 cm. Engine build and all eight full-reach structural checks pass.
The defensive filter retains the existing 192-ray refresh budget, and missed
probes are retried when tagged terrain arrives. These checks do not validate
all shoreline locations or long-run streaming. Survey navigation anomalies
remain at two stations. Source logs: `TroublemakerTerrainProbe.log`,
`TroublemakerTerrainFiltered.log`, `TroublemakerNoStaticCollision.log`.

![Collision-corrected side view](images/2026-09-05-troublemaker-water/troublemaker_no_static_collision_001_08360m_side.png)

The rendered bank still has large angular slivers; successful centreline
queries are not visual shoreline acceptance. Added a default-off, South
Fork-only `raftsim.SouthForkCrestSpray` A/B switch, reusing wet support-height
attachment and horizontal source planes without changing emitter budgets or
particle assets. At the same three stations it removes the detached plume
next to the raft, but leaves the main hole visually too quiet. Generic
particles are still not the ballistic Chilko variants. Do not promote this
switch or call the scene photorealistic. Log: `TroublemakerCrestSpray.log`.

![Wet-crest-attached spray experiment](images/2026-09-05-troublemaker-water/troublemaker_crest_spray_001_08360m_side.png)

An additional same-station ablation sets `RaftSimLocalFluidWPOStrength=0`
after three seconds. The material probe confirms zero on the visible V4
carrier. Inspected 8360 m side view: the large angular shoreline patches
remain. Shader micro-relief reopening CPU-collapsed triangles is therefore
not their main cause in this view; investigate the base carrier/wet boundary
next. This zero-displacement override is not retained. Log:
`TroublemakerNoShaderRelief.log`.

An isolated performance soak with the collision fix and default spray/wave
settings measured 668 frames: mean wall 29.943 ms, p95 wall 43.731 ms,
mean solver step 10.346 ms. No concurrent solve/build/capture ran. Compared
with the prior diagnostic's 29.254/43.135/10.351 ms, there is no demonstrated
performance improvement; the 16.67 ms frame and 1.6 ms solver budgets still
fail. Evidence: `performance-no-static-collision.json`. This is still an
offscreen Development diagnostic, not release qualification.

Next: inspect base-carrier wet/dry vertex geometry and compare its boundary
with actual terrain at the visible bank slivers; repair that before adding
foam or spray. The main hole still lacks the reference's steep dark face and
attached white breaking roller. No scene is accepted as photorealistic, and
the all-scenes goal remains active.

After updating the Chilko structural guard to retain its independent switch
under the new map-scoped South Fork experiment, all **45** plain checks across
the seven presentation/diagnostic test files pass. No game, build, or offline
solver process remains running at this checkpoint.

### Bed-aligned terrain comparison (following checkpoint)

Previous goal turn: progress, with a verified collision/query fix and visual
ablations. This turn inspected the current source and confirmed no process
was still running before starting new work.

Added a default-disabled, non-shipping one-shot `raftsim.ShorelineProbeStation`
diagnostic. At station 8359.5 m, the outer present vertices at lateral −7.5
and +22.5 m end 0.900 and 0.939 m above the actual terrain after their
1.275 m outward extension. Their solver depths are only 0.370 and 0.436 m.
The dry vertices collapse to these exposed edges. The mismatch is therefore
not just opacity or foam: the carrier's hydraulic bed and scenery bed differ.
Source: `TroublemakerShoreGeometry.log`. The first version's self-disable
used lower console priority and repeated logging; corrected to SetByConsole.
The later successful run logs only the requested row once.

The full-reach scenery imports a four-metre procedural terrain PNG, whereas
the rapid uses a separately shaped half-metre bed. Added
`RaftSim.ReviewTroublemakerTerrain`, compiled only in editor builds, which
duplicates **only** `SM_south_fork_02_Terrain` into the transient package,
aligns its intended rapid-region heights with sampled solver **bed** (not
water height), feathers the perimeter, rebuilds normals and collision, and
installs the copy for that process. It never saves the map or source asset.
The original terrain-grid density is retained in this initial comparison.

Two failed setup attempts are retained as evidence, not treated as captures
of a changed scene. The first command was in an editor module absent from
the `-game` run; moved the diagnostic into the runtime-loaded module behind
WITH_EDITOR. The second correctly rejected a proposed 7.517 m excavation.
Its coordinate audit proved a nearest-axis ambiguity: an original vertex
at (station 8472, lateral 84) projects onto (8332, −14.061) around the bend.
The source UVs reconstruct its original coordinates exactly (zero measured
XY error). The diagnostic now uses those original row/column coordinates,
not nearest-axis projection; the five-metre safety limit is unchanged.
Logs: `TroublemakerBedAlignedTerrain.log`, `TroublemakerBedAlignedRuntime.log`,
`TroublemakerBedRejection.log`, `TroublemakerCoordinateAudit.log`.

The corrected run **installed one transient mesh**, changing 732 vertices
with maximum absolute height change 2.420 m. Centreline terrain at
8348/8360/8372 m is 20018/19965/19917 cm, within 3/2/2 cm of the sampled
solver bed at those stations. At the same shoreline row, clearances change
from +0.900/+0.939 m to −0.200/+0.331 m. The first edge is now behind terrain;
the opposite edge still hangs above it. Source:
`TroublemakerAuthoredBedAlignment.log`.

![Temporary bed-aligned terrain, side](images/2026-09-05-troublemaker-water/troublemaker_authored_bed_alignment_001_08360m_side.png)

![Temporary bed-aligned terrain, approach](images/2026-09-05-troublemaker-water/troublemaker_authored_bed_alignment_000_08348m_chase.png)

Inspected both images against the earlier same-station captures: the large
hanging sheet behind the raft is mostly occluded by a continuous bank, but
stepped edges, far-bank slivers and detached spray remain. This is useful
evidence for a shared terrain/hydraulic bed, not a photorealistic result.
The diagnostic does not yet invalidate previously successful bank-height
cache entries after installing the mesh; direct survey traces are fresh, but
the runtime film-cull cache must be refreshed in a subsequent terrain trial.
Do not promote the transient mesh or use these build-time captures for FPS.

The three authored flow-band bed arrays are byte-value-identical (numpy
array equality); this permits a shared bed-aligned terrain but does not
validate their different water levels. Engine build succeeds and all 46
plain presentation/diagnostic checks pass. No production hydraulic arrays or
saved terrain assets changed in this turn.

Next: construct a finer local terrain patch with shared bed samples and
continuous perimeter, refresh terrain-probe caches after installation, then
repeat the same side/approach views and a moving shoreline sequence. Keep
the real reference's rock-confined breaking hole as the visual target; bank
alignment alone does not create its missing steep face, frothy roller or
recirculating motion. The all-scenes goal remains active.

### Local half-metre terrain and measured physical shallows

Previous turn: progress, with bed/terrain measurements and a verified transient
alignment comparison. This pass refines only the local rapid terrain patch.
Three shared-midpoint subdivisions turn 2,880 selected source triangles into
184,320 triangles (four-metre grid edges become half-metre edges). A zero-weight
perimeter retains original linear coarse edges. Other tile geometry, UV
channels, colours and material groups are retained. The first attempt hit an
engine tangent-build assertion because deleted parent triangle IDs remained
sparse. Explicit mesh compaction fixes the build; the failed run is preserved
in `TroublemakerFineBedTerrain.log`, not used as visual evidence.

The corrected refinement installed one transient terrain mesh, changing
49,197 vertex heights with a 2.606 m maximum absolute change. It also clears
successful and missed terrain-probe caches after replacement, so the next
bounded refresh measures the new terrain. Original assets remain unsaved.
`TroublemakerFineBedCompact.log` confirms installation and successful capture.
The opposite water edge still hung 0.331 m above ground: more terrain vertices
alone did not repair the wet/dry decision.

Two legacy compatibility rules caused the remaining cutoff. The first
suppressed live shallow cells below 0.35 m when an older baseline said dry;
the second culled the last shallow row and shortened the bank extension.
Both now defer to the live wetting front **only after a successful terrain
measurement agrees with the hydraulic bed within 10 cm**. Unknown or
mismatched terrain retains the old protection. Additional requested probes
share the existing 192-ray budget. The live physics field is not altered.

At station 8359.5 m, the opposite boundary progresses from lateral 22.5 m
with a 0.939 m original gap, through 25.5 m with 0.204 m gap after the first
rule change, to lateral 28.5 m with **0.012 m actual terrain clearance** after
both changes. The 27 m row has 0.037 m clearance. Logs:
`TroublemakerMeasuredShore.log`, `TroublemakerPhysicalShallows.log`.
This proves a local alignment improvement, not every shoreline vertex.

The 8360 m side image still has angular bank shapes elsewhere, smooth pale
swells and detached spray. It does not resemble the reference's rock-confined
steep dark face and attached white breaking roller sufficiently for acceptance.
The refined terrain remains a transient experiment; no saved terrain or
production cooked fields were promoted.

An isolated unchanged-terrain performance soak of the runtime shallow-water
rule, at the established 8358 m/1280×720/12-second warmup/20-second sample,
measured 658 frames: mean wall 30.428 ms, p95 44.569 ms, mean solver step
10.143 ms. It still fails both budgets and demonstrates no frame-time gain.
It does not measure the refined terrain's runtime cost. Evidence:
`performance-measured-shallows.json`.

The first moving sequence requested 60 images but wrote only 51: repeating
timers can fire repeatedly in a hitch before rendering, overwriting Unreal's
single pending screenshot request. The capture helper now waits when a
request is pending and logs actual request timestamps/frame numbers. The
incomplete run is retained as diagnostic evidence, not a full 60-frame clip.
Inspected frames 000/030/050: visible motion, but continued broad pale swells,
angular banks and spray not convincingly attached to a breaking face.

The corrected run wrote **60/60 images**. Actual screenshot request times
span world seconds 10.035–24.318 (14.283 seconds, not the nominal 11.8-second
interval span). Capturing is too expensive to use this sequence as a frame-time
measurement. Render-state logs contain only the initial grid recenter/core
creation at world second 0.397; there is no moving-window handoff during the
captured interval, so it does not validate that transition.

Inspected corrected frames 030 and 059: camera travel is evident, but broad,
smooth pale swells, angular exposed banks, and detached airborne sprite
clusters remain. Against the previously inspected real Troublemaker reference,
the steep rock-confined face, dense attached breaking roller and foam volume
are still missing. No visual or animation acceptance is recorded.

![Measured physical shallows, 8360 m side](images/2026-09-05-troublemaker-water/troublemaker_physical_shallows_001_08360m_side.png)

![Corrected moving sequence, frame 030](images/2026-09-05-troublemaker-water/troublemaker_shallows_motion_complete_030.png)

![Corrected moving sequence, frame 059](images/2026-09-05-troublemaker-water/troublemaker_shallows_motion_complete_059.png)

Verification checkpoint: editor Development build succeeds; 49 plain
presentation/diagnostic checks pass; `RaftSim.P2.WaterSurfaceRenders` passes in
`WaterSurfaceAfterMeasuredShallows.log` with exit status 0. Its existing
`r.MotionVectorSimulation` render-thread-safety warning remains; passing this
test does not resolve that warning or certify temporal quality. No Unreal
process remains after the test. No saved terrain or production hydraulic fields
were changed or promoted, and no commit/push was made. The all-scenes goal
remains active. Next work must address the missing hydraulic face/roller and
attached falling spray while preserving these bank measurements and checking
the still-failing performance budget.

### Local falling-spray source review

Previous goal turn: progress, with completed motion evidence and an engine
regression pass. This turn tests `-RaftSimSouthForkBallisticSpray`, restricted
to FullReach and the normal (non-photographic-review) asset roster. It reuses
the existing Chilko falling roller/droplet assets without modifying them or
increasing emitter budgets. Defaults for all scenes remain unchanged.

Source inspection distinguishes the particle populations: legacy aerosol has
slight upward acceleration; legacy roller gravity is −260 cm/s² and crest
spray gravity is already −980 cm/s². The latter still has large, velocity-aligned
sprites and short lives. The reused profiles have smaller unaligned sprites,
−980.665 cm/s² gravity and lives long enough for a vertical ballistic return
at their configured maximum initial speeds. This does not establish observed
particle return/impact or turbulence fidelity.

The first 40-frame comparison (`TroublemakerFallingSprayReview.log`) removed
the obvious foreground fountains but looked nearly spray-free. A one-time
source audit (`TroublemakerSpraySourceAudit.log`) found 19 published sites but
only three eligible sources, all at 8454–8455.5 m, around 100 m downstream.
Their support approximation was 0.605–0.775 m below their published optical
positions. Projection matched known river coordinates at these measured
sources; this particular failure was **not** nearest-bend misprojection.

The geometry-carve budget favoured stronger distant sites and its weight was
also gating local spray. Added a separate published persistence envelope for
the review's existing nearest-six particle budget; physical relief and its
ranking remain untouched. The next comparison (`TroublemakerLocalFallingSpray.log`,
40/40 files) selected nearby sources at 8358–8374.5 m, four emitting at the
10-second audit. Published optical positions were retained instead of moving
them to approximate raft-support heights. Inspected frames 000/020/039: lower,
smaller spray returned, but frame 020 still shows bursts over exposed bank.
This intermediate state is not accepted or promoted.

The subsequent correction samples the currently interpolated carrier triangles
at the known river coordinates, with the exact mesh diagonal, and checks the
centre plus four points spanning the bounded source strip. It rejects non-live,
culled, less-than-10-cm-deep or known buried vertices. Eligibility retains one
byte per vertex from the existing refresh. Runtime VFX lookups add no terrain
raycasts or new physics queries; raft-support sampling runs only in the one-time
comparison audit. This query excludes material-only WPO and is presentation
only. It does not claim exact particle collision with an animated crest.

The first build of that query correctly failed: solver samples/wet masks are
refresh-local, not actor members. The explicit small cached eligibility mask
fixes that ownership error. The successful build is the basis for subsequent
captures; the failed build is not treated as verification. Re-inspected the
user-provided real whitewater image this turn: its steep green face and dense
attached white pile are still conspicuously absent from these smooth pale
game swells. Spray source repair alone is not the final visual target.

Final moving comparison for this turn: `TroublemakerCarrierFallingSpray.log`
and `troublemaker_carrier_falling_spray_000..039.png` contain 40/40 captures,
world seconds 10.042–19.231. Inspected frames 000/020/039 against the preceding
run and the supplied reference photograph. The earlier obvious bank bursts
are absent in these inspected frames; two nearby sources remain enabled at
8358 m. Four source footprints are rejected. Their zero logged carrier height
means **lookup failed**, not a water elevation of zero. The two accepted
carrier elevations are 201.010 and 201.262 m, respectively 11 and 18 cm above
their pre-final-carve published site heights. This validates using the current
carrier instead of either preliminary site height or the support approximation.
The test samples footprint centre/cardinal extents, not every interior point,
and does not prove that all moving particles remain off shore.

![Intermediate local spray still over bank, frame 020](images/2026-09-05-troublemaker-water/troublemaker_local_falling_spray_020.png)

![Carrier-checked local spray, frame 020](images/2026-09-05-troublemaker-water/troublemaker_carrier_falling_spray_020.png)

![Carrier-checked local spray, frame 039](images/2026-09-05-troublemaker-water/troublemaker_carrier_falling_spray_039.png)

An isolated combined refined-terrain/spray soak, no screenshots, 1280×720 at
87% screen percentage, 20-second warmup and 20-second measurement, recorded
672 frames: mean wall **29.789 ms**, p95 **44.225 ms**, mean solver **10.039 ms**.
Both budgets still fail; 271 frames exceed 33 ms. This differs from the older
unchanged-terrain/12-second-warmup protocol, so it is not a clean per-feature
performance A/B. It demonstrates no unacceptable multi-second slowdown in
this run, not playable-release performance or an FPS improvement. Evidence:
`performance-carrier-falling-spray.json`.

Verification: Development build succeeds, 53 plain checks pass, and all three
engine tests in `CarrierSprayRegression.log` pass: `RaftSim.M5.ChilkoBallisticSpray`,
`RaftSim.M5.RapidSourceBinding`, `RaftSim.P2.WaterSurfaceRenders`. The numerical
triangle test covers weights/diagonal/linear grades, not all rendering or wetting
states. No Unreal process remains after tests. No assets, defaults or cooked
fields were promoted; no commit/push. The review flag remains opt-in.

Next actionable finding: the same global strongest-site geometry weighting
that selected the distant runout also excludes nearby detected jumps from the
main crest/pocket geometry. Audit spatially local relief evaluation without
making raft support depend on camera position or multiplying every vertex's
expensive work. Then re-check the actual hole's face, roller and white-water
volume against the reference. No scene is accepted as photorealistic; the full
all-scenes goal remains active.

### Spatially local breaking geometry

Previous goal turn: progress, with measured spray-source correction, motion
captures and performance evidence. This turn adds FullReach-only opt-in
`-RaftSimSpatialBreakingReview`. Instead of selecting only the three globally
strongest pocket/crest owners, every persistent accepted jump can retain its
eased weight. Camera position does not enter that selection. The 24-site
persistent-registry cap remains; this does not make unbounded new detections.

The renderer bins the sites by station before evaluating expensive profiles.
Each row receives only sources whose support interval can reach it; lateral
checks/fades remove unrelated sources before pocket/boil/roller work. The
presentation fade has continuous edges at −32/−30 m, 20.5/23 m and lateral
10/12 m. The authoritative water samples are unchanged. Raft support receives
the same full set of shared crest definitions; row binning is an evaluation
optimization, not a camera-dependent physical-wave budget.

A second defect appeared in the shared evaluator: a distant tall wave raised
the cap on overlapping small local crests despite contributing zero local
height. The review's `bLocalEnvelopeCap` calculates the overlap cap from local
enveloped amplitudes only. Its default is false, retaining the legacy path
outside this comparison. The engine `SpatialBreakingLocality` test now checks
distant downstream/lateral independence, bounded continuous local response,
legacy-profile local caps and full-set versus station-subset height/foam.

The first before-fix test crashed because its fixture appended an array's own
element directly back into that array; Unreal forbids that alias. The fixture
now copies it first. `SpatialBreakingLocalityBefore.log` is therefore a test
harness failure, not evidence for the rendering defect. The corrected
`SpatialBreakingLocalityRed.log` records actual failed locality assertions
against the old evaluator (its process exit code was 0 despite test failure).
After the evaluator correction, both `SpatialBreakingLocality` and
`HydraulicCrestScale` pass in `SpatialBreakingLocalityAfter.log`. A float/double
template build error in the spatial fade was also corrected before captures.

The first spatial capture (`TroublemakerSpatialBreaking.log`, 40/40 images)
showed only a slight foam change, not the intended crest improvement. Source
inspection corrected the previous working hypothesis: **South Fork's existing
path did not use shared depth-scaled crests at all**; that gate was Chilko-only.
The global three-site cap affected its pocket/boil geometry, while raw fixed
lift still drew its crests. The spatial review now explicitly enables shared
render/support relief, rather than merely publishing physical dimensions that
the old South Fork path never consumed. Defaults on other scenes are unchanged.
The first capture is retained as incomplete wiring evidence, not acceptance.

The corrected shared-path run is `TroublemakerSpatialSharedCrests.log`:
40/40 images spanning world seconds 10.065–19.127. Inspected frames 000/020/039
against the prior captures and the previously inspected real-whitewater
reference. Nearby sources at 8358 m have geometry weight 1 and unresolved
crest dimensions of 0.171/0.250 m. The centre carrier/support elevations are
201.083/201.078 m, but the off-centre source remains 201.332/201.053 m—a
**0.279 m discrepancy**. The shared-component regression does not prove full
surface parity: optical smoothing, shoreline treatment, interpolation and
material-only displacement still differ. Do not generalize the centre match.

At the measured 8359.5 m cross-section, lateral 27 m has 0.038 m terrain
clearance; lateral 28.5 m and its collapsed dry continuation retain 0.011 m.
Thus this local shoreline repair survived the new crest trial. Broad swells,
weak visible aeration and angular bank shapes remain. The change is not the
steep rock-confined face, attached frothy pile or convincing breaking motion
in the reference, and no photorealistic acceptance is recorded.

![Shared spatial crests, frame 000](images/2026-09-05-troublemaker-water/troublemaker_spatial_shared_crests_000.png)

![Shared spatial crests, frame 020](images/2026-09-05-troublemaker-water/troublemaker_spatial_shared_crests_020.png)

![Shared spatial crests, frame 039](images/2026-09-05-troublemaker-water/troublemaker_spatial_shared_crests_039.png)

The same combined refined-terrain/spray protocol as the preceding comparison
(20-second warmup, 20-second sample, 1280×720, 87% screen percentage, no
screenshots or concurrent engine work) measured 666 frames: mean wall
**30.040 ms**, p95 **43.136 ms**, mean solver **10.256 ms**, 272 frames over
33 ms. Previous values were 29.789/44.225/10.039 ms. This single pair shows
no meaningful average-frame improvement or severe new slowdown; both budgets
still fail. Evidence: `performance-spatial-shared-crests.json`. It is not
packaged, focused, release-performance qualification.

Verification checkpoint: build succeeds; 56 plain checks pass; the final
`SpatialSharedCrestsRegression.log` records successful `HydraulicCrestScale`,
`SpatialBreakingLocality` and `WaterSurfaceRenders` tests. No new saved assets
or production cooked fields were promoted. Both spatial breaking and the
falling-spray comparison remain explicit opt-ins. No commit/push was made.

Next: the physical channel and inflow must produce the reference's hole,
not merely a smooth low-Froude swell. Revisit the rejected narrow-throat cook
using its measured discharge deficit and inlet-boundary implementation;
verify a consistent imposed flow before further channel-shape comparisons.
Keep the spatial/shared support regression and shoreline measurement as
guardrails. Off-centre full-surface parity and performance remain open.
No river scene meets the full photorealistic rendering-and-animation goal.

## Inlet discharge audit and constant-flow experiment

The saved 288-second channel trials were inspected through the **actual C++
MUSCL face reconstruction and Riemann flux routine**, not a cell-centre h*u
approximation. `inspect_boundary_mass_fluxes()` evaluates that routine at dt=0
into scratch state, with positive flux defined into the domain. It is an explicit
offline diagnostic, never called by normal stepping. CLI `--inspect-boundary-flux`
prints JSON and exits without advancing or writing a simulation. The companion
`physics/scripts/inspect_hydraulic_boundary_flux.py` validates any saved frame
against its exact bed/grid and records the command and provenance.

| Saved state | Target metadata Q | West ghost h*u Q | Actual west face Q | Actual east outward Q | Net volume rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original channel, 288 s | 45.307 | 45.307 | 43.001 | 41.772 | +1.229 |
| Interpreted 12 m throat, 288 s | 45.307 | 45.307 | 32.851 | 30.073 | +2.777 |

All fluxes are m³/s. Median inlet water level above the prescribed stage is
0.0192 m in the original channel and 0.1002 m in the throat trial. Thus the
throat trial did **not** compare channel shapes at equal discharge. The current
stage-plus-velocity ghost boundary responds to backwater by reducing its
numerical inflow. The metadata target is not an enforced flux, and neither
snapshot is exactly steady. This is a boundary-condition mismatch for the
intended constant-flow comparison, not evidence of water disappearing internally.
The distinction between a flow and a stage boundary is also documented in
[USACE's external-boundary guidance](https://www.hec.usace.army.mil/confluence/rasdocs/r2dum/6.3/boundary-and-initial-conditions-for-2d-flow-areas/external-boundary-conditions);
that source does not validate this project's solver or interpreted channel.

An explicit offline `--experimental-west-discharge` option now supports a
constant net west discharge in the uncalibrated second-order scenario-boundary
path. It distributes Q by wet depth-based conveyance, preserves the outgoing
characteristic u−2√(gh), solves for free inlet depth, and applies physical face
fluxes directly. The existing inlet stage defines its fixed wet cross-section
only, not the evolving water level. Adjacent dry-bank portions of the external
boundary are reflective. Supercritical outgoing fringe flow is extrapolated and
accounted for in the net inflow; unsupported supercritical incoming flow is rejected.
This is not a general hydrograph, dry-start inlet or calibrated production boundary.
No informational discharge metadata implicitly enables it. Game defaults remain off.

The first time-running attempt correctly stopped at a nearly dry outward-draining
cell (row 35, h≈0.000001 m, u=−0.129645 m/s, time 0.68 s). Handling outgoing
characteristics exposed another invalid inlet segment: row 117 was outside the
authored wet cross-section and developed a thin incoming bank film (h=0.000346 m,
u=0.231990 m/s, time 2.30 s). The fixed wet inlet footprint addresses this without
removing the supercritical-inflow guard. Both unsuccessful trials are retained;
neither generated accepted hydraulics or imagery.

Native tests cover flux signs/units, wall impermeability, non-mutating inspection,
small-step volume balance, the stage-boundary backwater response, exact constant-Q
response to backwater, unchanged matching uniform flow, outgoing fringe accounting,
dry-bank exclusion and rejection of unsupported modes/supercritical inflow.
The native lake-at-rest fixture suite and 57 plain scene/audit checks pass.
The revised 12 m trial completed 96 more simulated seconds (288→384 s) in
424.956 wall seconds: `tmp/troublemaker-throat12-fixedQ384-footprint`.
Its final actual west face flux is **45.3069545472 m³/s**; east outward flux is
**36.1843 m³/s**, leaving **+9.1227 m³/s** instantaneous storage. Inlet median
stage is now 0.1975 m above the old prescribed stage. Total volume increased
from 22,506.562 to 23,761.733 m³; the final 9.6 s interval still accumulated
109.943 m³. This state is **not steady** and cannot yet compare channel shapes
at equal through-discharge. Hole section Q at 8362 m rose from 32.169 to
37.488 m³/s; the broad hole-region median speed rose from 1.393 to 1.551 m/s.
At |lateral|<3 m, median stage rises only 0.0659 m between 8358 and 8362 m,
still a weak recovery rather than the reference's strong breaking hole.
The generic validation passed but maximum speed was 45.104 m/s in thin water;
the final snapshot's maximum at depth>0.1 m is 8.417 m/s. Neither is a visual
or physical-calibration acceptance criterion.

Evidence JSONs: `boundary-flux-baseline288.json`,
`boundary-flux-throat12288.json`, `boundary-flux-throat12384-fixedQ.json` and
`hydraulic-spinup-throat12-fixedQ384.json` in this report's image/evidence folder.
No new production fields or saved assets are promoted, and no new scene images
are claimed from this offline trial. The next hydraulic comparison requires a
settled constant-Q throat and an equal-flow original-channel control before any
terrain/whitewater promotion. In-game rendering, animation and performance
remain unaccepted across every scene.

Interface verification after this experiment: rebuilt `physics/cpp/build-ue/raftsim_water.lib`
with `unreal/Scripts/build_solver_lib.ps1`, then rebuilt the Win64 Development editor
(success). This avoids linking the changed `SolverConfig` layout against a stale
archive. `BoundaryFluxInterfaceRegression.log` records successful
`RaftSim.P2.HydraulicCrestScale`, `RaftSim.P2.SpatialBreakingLocality`, and
`RaftSim.P2.WaterSurfaceRenders` tests after relinking. All 57 plain checks and
`git diff --check` pass. No experimental inflow is enabled by any scene default.
No new performance result or photorealistic imagery is claimed for this checkpoint.

## Constant-flow 576-second trial and corrected hole framing

The interpreted 12 m throat completed another 192 simulated seconds (384→576 s)
in 1,371.033 wall seconds. Exact final boundary flux is west +45.3069545472,
east outward 42.917694, sides zero, leaving +2.389261 m³/s instantaneous storage.
Volume is 24,892.1784 m³. The 8362 m section carries 43.18077 m³/s, versus
37.488 at 384 s. Hole-region median speed is 1.640 m/s; its supercritical wet
fraction is 0.140. Central |lateral|<3 m median stage recovers only 0.10067 m
between 8358 and 8362 m. This is still not the strong reference roller.

`assess_troublemaker_convergence.py` now screens the last four saved samples
for section discharges within 5% of target, interval storage below 2% of target,
and regional median stage ranges below 1 cm. These are explicitly diagnostic
thresholds chosen for this experiment, not measured river uncertainty or visual
acceptance. The 576 s state fails discharge (maximum relative error 7.369%) and
storage (8.790%); stage ranges pass (maximum 0.9547 cm). Generic native validation
passes; maximum final speed in depth>0.1 m is 9.413 m/s. Neither result is physical
calibration. Evidence: `hydraulic-spinup-throat12-fixedQ576.json`,
`boundary-flux-throat12576-fixedQ.json`, `convergence-throat12-fixedQ576.json`.

The isolated review exporter now accepts the exact declared interpreted-throat
bed, validates grid/river/band/datum/boundaries and the source solver manifest,
and requires explicit source provenance for changed beds. Wrong or unrelated
beds are rejected. Output remains under `tmp`, never shipped fields. The exported
576 s review package preserves the changed bed and records the offline constant-Q
configuration. **The live game still evolves a cropped, first-order solver with
its existing edge conditions; it does not replay the offline constant-Q inlet.**
This distinction is recorded in the review manifest rather than silently claiming
the two simulations are identical.

A repeated boat-view capture exposed a review error: with spawn station 8350 m
and ten seconds of warm-up, the first screenshot was already at **8369.934 m**,
beyond the 8358–8362 m central hole. Thus those delayed downstream views were
not fair close-ups of the hole. This new measured reproduction does not establish
the unlogged exact positions of every historical capture. `CaptureSeries` now
logs actual raft station/lateral, camera world position, validity, frame index,
and game time for every accepted request. New `river_station`,
`river_station_downstream`, and `river_station_side` presets frame an explicit
`focusstation`/`focuslateral` without teleporting or freezing the raft or water.
Invalid/dry focus refuses a fallback capture.

The first new fixed-camera implementation incorrectly fed world-space water
height into the source-datum conversion and landed underwater. Its failed
`TroublemakerFixedQ576Hole.log` and screenshots are retained but excluded from
visual conclusions. The correction resolves mapped XY and assigns sampled world
Z exactly once. The rebuilt editor and new coordinate/source guards pass.

Corrected focus: station 8360 m, lateral −1.5 m. A downstream camera is 8.5 m
away and 2.4 m above sampled water, looking back at the hole. Four reviewed
sequences each have 40/40 distinct PNGs, zero logged camera displacement and
8.85–8.96 seconds between first/last requests. Actual screenshot request intervals
are roughly 0.19–0.40 s, not guaranteed 0.2 s or native gameplay frame cadence.
`audit_water_capture_series.py` checks file/request correspondence, advancing
times/frames and positions, hashes every PNG, and reports adjacent-frame ROI pixel
differences. These establish changing sampled pixels, **not** correct flow,
spray return trajectories, absence of flicker, or playable FPS. No new isolated
performance run was made here.

Qualitative ablations with the same input field and fixed focus:

| Review | Observation | Decision |
| --- | --- | --- |
| Default 16 optical passes, foam gain 0.95 | A deep rock-adjacent depression is visible, but broad smooth glossy water and sparse foam persist. | Not realistic. |
| Foam intensity temporarily zero | Much of the brightest white remains; this is glare, not a thick foam body. | Diagnostic only. |
| One optical pass; four-pass hydraulic sources unchanged | More of the rock/channel shape is exposed, but the breaking roller is still absent and bank edges remain coarse. | No default promotion. |
| Foam coverage gain 3.5 | More connected white flecks, still mostly flat surface marks rather than piled, overturning froth. | No default promotion. |
| Side view of gain 3.5 | Clearly shows insufficient roller volume and discrete spray plumes instead of coherent crest collapse. | No default promotion. |

Selected actual images: `hole-fixedQ576-baseline.png`,
`hole-fixedQ576-nofoam.png`, `hole-fixedQ576-smooth1.png`,
`hole-fixedQ576-foam35.png`, `hole-fixedQ576-side35.png` in the evidence folder.
Paired `capture-fixedQ576-*.json` records preserve the instrumented sequences.
The real user photo and paused 35/40 s frames of the supplied Troublemaker video
show much denser white piles and steeper, irregular green faces. Attempts to
revisit continuous reference playback encountered ads/autoplay; unrelated footage
was not relabelled as Troublemaker or treated as new motion validation.

65 plain scene/export/convergence/capture checks pass. The camera-only changes
build successfully in the Development editor. Original-channel equal-inflow
control is the next numerical comparison; no material parameter experiment,
interpreted terrain, or new hydraulic field is promoted to production. All scenes
remain short of the rendering, animation and performance goal.

## Equal-inflow original control and throat bypass finding

The original-bed control completed 96 additional simulated seconds (288→384 s)
in 662.935 wall seconds. Its exact final west flux is 45.3069545472 m³/s,
east outward is 43.852168, and net storage is +1.454786. At station 8362.089 m,
section Q is 43.789904 m³/s; the narrowed 576 s trial has 43.18077 at the same
section. These through-flows are now close but not identical, and both states
remain transient. The original control's last-four-sample screen fails the
5% section-Q criterion (5.306%) and 2% interval-storage criterion (6.066%),
while stage ranges pass (maximum 0.8336 cm). Hole-region median speed is
1.44766 m/s, Froude p99 is 0.75176 and supercritical wet fraction is zero.
Generic solver validation passes; that does not establish realistic whitewater.

Exported original control to `tmp/troublemaker-review-original-fixedQ384` and
captured the same explicit downstream hole preset at 8360 m, lateral −1.5 m.
Camera elevation tracks this input's local water level, so it is 0.244 m higher
than the narrowed trial, not a pixel-identical photographic pose. The raft is
also still in view: its logged range is 8362.014–8365.482 m, unlike the faster
narrowed trial, and it partly occludes the hole. All 40 frames exist with distinct
hashes, zero camera displacement and 8.905 seconds between first/last requests.
The image remains a glossy rock-adjacent depression with sparse spray, not the
reference's dense roller. Evidence: `hole-original-fixedQ384.png`,
`capture-original-fixedQ384.json`, `hydraulic-spinup-original-fixedQ384.json`,
`boundary-flux-original384-fixedQ.json`, `convergence-original-fixedQ384.json`.

Inspection of transverse section fluxes exposes a flaw in the **experimental
throat authoring**, not a new solver mass-loss bug. Using each snapshot's exact
cell-centre `hu * dy` (dy=0.5 m) and the existing S-bend centreline, at station
8358.089 m the narrowed trial carries total Q=42.908 m³/s, only 34.493 within
±6 m of centre, and 8.022 outside ±9 m. At 8362.089 m, 8.032 of 43.181 m³/s
is outside ±9 m. Approximately 19% therefore bypasses the intended 12 m throat.
The original channel at 8358.089 m has total Q=43.630 and 6.053 outside ±9 m.
The trial's raised shoulders are weighted by **original wet depth**, leaving
adjacent originally dry low ground untouched. They can become islands with
parallel side channels as the inlet stage rises. The in-game side view is
consistent with this measured bypass; no claimed surveyed bank geometry exists.

Next hydraulic work should test shoulders connected continuously into sufficiently
high banks, with an explicit new experiment identity and bounded terrain changes.
Do not modify the existing throat generator in place and invalidate all its
recorded source-bed comparisons. The connected variant has **not** been implemented
or simulated at this checkpoint. Further increases in foam coverage are not an
adequate replacement for resolving this channel-control defect. No new production
fields, terrain or material defaults were promoted, and no scene is accepted.

Follow-up: [bank-connected throat and recording-timing review, September 6](2026-09-06-troublemaker-connected-throat-review.md).
