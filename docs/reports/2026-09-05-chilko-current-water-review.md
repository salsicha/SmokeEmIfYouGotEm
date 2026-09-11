# Chilko / Lava Canyon water review — 2026-09-05

Result: improved surface presentation and performance, **not photoreal acceptance**.
Inspected actual `/Game/RaftSim/Maps/L_LavaCanyon` gameplay. This pass changes
Chilko's live material and presentation budget, not its terrain, hydraulic cook,
raft forces, obstacle collision, lighting, or map. Unrelated working-tree changes
were preserved. Nothing was committed or pushed.

## Findings and retained changes

The baseline rapid looked like a dark blue, nearly unbroken sheet. The live map
already used one visible water surface. Initial telemetry measured a 0.2614
aeration maximum, which the inherited material cutoff suppressed:
`0.2614 * 0.9 - 0.28 < 0`. This is an initial-frame observation, not a maximum
over the whole run. The first 92,833-vertex presentation refresh cost 69.9 ms.

- Saved an isolated `M_RaftSim_ChilkoCurrentWaterV4` parent on the existing
  `MI_RaftSim_ChilkoLavaCanyon_LiveVolumeWaterV2`. Refreshed its two existing
  river-local texture dependencies. The static preview water remains unchanged.
- Replaced the active directional normal-texture input with two rotated scales
  of analytic triangular-gradient noise. The shader uses integrated current
  displacement and pixel-footprint filtering, not independent sine-wave clocks.
  Chilko opts into the previously reviewed Futaleufú kernel; other rivers'
  shader variants were not regenerated in this pass.
- Set normal strength to 0.18, resolved-aeration cutoff to 0.045, foam coverage
  gain to 4, and foam core gain to 1.8. Disabled speed-only whitening. Existing
  persistent foam transport and coupled geometric relief remain active.
- Tested additive foam-breakup biases of 0.15 and 0.03 in temporary processes.
  Rejected both: the first became a white blanket; the second added a gray veil.
  Retained zero bias and a Chilko-only lace modulation floor of 0.10 instead of
  0.02. This reinforces froth inside the broken web while retaining dark gaps.
  It does not create entrained-air volume or independently simulate breaking.
- Capped single-surface Chilko presentation at 1 m spacing (23,377 vertices),
  about 75% fewer vertices. The underlying hydraulics are unchanged. This has
  a sampling cost: initial sampled relief peak changed from 0.2656 to 0.2108 m.
  It is not an identical-geometry optimization. The 0.78 relief scale and
  existing support coupling were retained. No second foam sheet was added.

## Gameplay inspection and limitations

Inspected an initial candidate at requested starts 24, 228 (normal launch),
300, 340, and 520 m, then checked the retained foam treatment at the approach,
launch, rapid, and recovery. Short-settle opposite-side series at 300 and 340 m
give closer views of the main rapid and lateral wave. These are walk destinations:
the raft keeps drifting during capture. They are not identical replay positions.

Early/late frames show evolving detail and intermittent spray without an obvious
whole-surface toggle in the sampled series. Eight frames spaced 0.3 seconds apart
are **not** high-frame-rate video validation or proof of stability over a whole run.
Final diagnostics confirm `singleSurface=1` and `rapid_foam_visible=0`.

The following remain unresolved:

- The froth still has an overly even, mottled distribution. Large curling and
  collapsing crests, piled aerated water, and convincing recirculation are missing.
  Better normal shading is not a substitute for those shapes.
- Bank-side relief remains angular. The short 340 m view also shows a wave
  obscuring much of the raft in a later frame; boat-to-visible-crest alignment
  needs further verification. No raft-support fix is claimed here.
- Spray looks like intermittent upright puffs rather than crest-driven sheets
  and droplets. No Niagara reauthoring was done in this pass.
- The historical September 2 inspection documented terrain/solver disagreement
  near 340 m and hydraulic shock pits. Neither was recooked here. These captures
  do not clear those defects or establish continuous shoreline quality everywhere.
- The straight interpreted 600 m reach and visible hard end are not a surveyed
  Lava Canyon reconstruction. The existing vegetation also remains stylized.
- Current-normal motion uses shared integrated advection, not a new per-pixel
  eddy solver. Existing local foam transport remains; accurate raft dynamics
  are not established by this presentation review.

## Performance

Before/after used the same editor-hosted Development, offscreen 1280×720 protocol:
87% screen percentage, medium quality, normal map launch, 12 s warmup and 20 s
sample. No build or other engine capture ran concurrently with either measurement.
This is an engineering diagnostic, not packaged-release qualification or a
deterministic trajectory replay. Both kept 27 production Niagara components;
the final sample had six active aerosol and six roller sites versus five each
in the baseline, so VFX was not disabled to obtain the improvement.

| Metric | Baseline | Retained |
| --- | ---: | ---: |
| Mean wall frame | 85.36 ms | 14.70 ms |
| Approximate mean FPS | 11.7 | 68.0 |
| p95 wall frame | 93.36 ms | 30.64 ms |
| Maximum wall frame | 102.33 ms | 38.09 ms |
| Frames over 33 ms | 235 / 235 | 25 / 1,361 |
| Mean render thread | 29.11 ms | 10.99 ms |
| Mean GPU | 27.01 ms | 8.19 ms |
| Mean solver step | 2.38 ms | 2.68 ms |
| Peak memory | 3,478 MB | 3,341 MB |

The frame and solver budgets still **fail**. This is not sustained 60 FPS.
The main remaining spikes are CPU-side; reducing presentation work did not
improve the solver's own cost.

## Verification and reproduction

- Win64 Development Editor build succeeded.
- Saved-material audit passed, including actual Normal connection, triangular
  shader kernel, cutoff, current advection, filtering, and scalar overrides.
- Unreal `RaftSim.M9.FChilkoLavaCanyonWater`: **Success**.
- 26 focused plain Python tests passed across Chilko, Futaleufú, Pacuare,
  Colorado, South Fork performance/banding, and full-reach presentation.
  The bundled runtime has no pytest; the legacy pytest suite was not run.
- Scoped tracked-source `git diff --check` passed (line-ending warnings only).

Capture helper: `unreal/Scripts/review_chilko_water.ps1`. Defaults take eight
frames at each requested station. `-CameraLateral -5 -SettleSeconds 1` gives the
closer lateral view. Asset audit: `unreal/Scripts/review_chilko_water_assets.py`,
run with Unreal `-ExecutePythonScript`; optional `-RaftSimRefreshChilkoWater`
rebuilds and saves only these scoped live-water assets.

Evidence is preserved in the adjacent `2026-09-05-chilko-current-water-review/`
directory: actual game PNGs, before/after performance JSON, material audit,
and the automation log. Candidate and rejected-probe images are labeled as such.

## Selected actual captures

Baseline, requested 300 m start:

![Chilko baseline](2026-09-05-chilko-current-water-review/before_300.png)

Retained material, same requested start and camera (not identical raft pose):

![Chilko retained](2026-09-05-chilko-current-water-review/retained_300.png)

Short-settle lateral view; this also documents the remaining angular banks:

![Chilko lateral wave](2026-09-05-chilko-current-water-review/retained_side_340_000.png)

## Photoreal goal: first follow-up checkpoint

The all-scenes goal is active; Chilko remains the first scene under review,
not an accepted scene. Next scenes are Troublemaker, South Fork full reach,
Colorado/Hance, Pacuare, Futaleufu, and Zambezi. No scene is declared photoreal.

Inspected the actual images in OARS' [big-water trip article](https://www.oars.com/blog/best-big-whitewater-rafting-trips-in-the-world/)
and [White Mile overview](https://www.oars.com/blog/10-of-the-worlds-best-whitewater-rapids/).
Also inspected paused frames at approximately 3:53.81, 3:54.84 and 3:55.84 in
[Veloci_Rafter's Chilko footage](https://www.youtube.com/watch?v=mA9YG8PDDr8&t=233s),
using browser frame stepping. These are qualitative references, not matching
camera/flow surveys or a complete footage review. The uploader describes 75 CMS;
the current median runnable cook uses 105 cubic metres per second. Reference
media remain external links, not copied project assets.

The photos have broad dark green-blue faces, irregular connected crest caps,
and substantial changes in wave height at raft scale. The sampled footage
shows changing broken crests and strong raft/camera pitch. Our captures still
show overly even fine froth, shallow-looking relief, and angular banks. The
change below is a correctness fix, not a demonstrated major visual improvement.

### Retained shared breaking profile

The visible lattice previously accumulated lift from raw jump detections before
deduplication, while raft support evaluated a different profile using persistent
accepted sites. Chilko's single-surface path now uses that same persistent
crest/toe/tail helper, eased site weight and relief scale. The visible shoreline
taper remains. Other scenes are unchanged; `raftsim.ChilkoSharedBreakingRelief 0`
restores the old path for comparison. Render-only plunge-pocket/boil displacement
and material WPO still exist, so this does **not** establish full surface/support
agreement. No new layer, hydraulic cook or terrain edit was introduced.

- Win64 Editor build succeeded; Unreal `RaftSim.P2.SharedBreakingRelief` passed.
  Its numeric checks cover crest/toe, lateral and longitudinal limits, eased
  intensity, sub-grid continuity, and overlap bounds. An initial test-fixture
  aliasing assertion was fixed before the successful rerun.
- 27 focused plain Python tests passed across the six existing water-review
  suites. These source/math guards are not visual acceptance tests.
- Capture timers now request at most one screenshot per rendered frame. Earlier
  0.1-second capture attempts produced only 23/26 of 48 files because catch-up
  callbacks overwrote pending requests. The corrected old/new runs each produced
  all 48 images, with world timestamps and render frame numbers in their logs.
  Disk readback slows these runs: **they are not 10 FPS real-time recordings**.
- Before/after use the same requested 340 m station and side camera, not a
  deterministic raft replay. First/last frames were inspected; the visible
  difference is modest and does not clear the missing large crest shapes.
- New matched engineering performance sample: 1,348 frames, mean wall 14.85 ms
  (67.3 FPS), p95 32.13 ms, max 36.06 ms, 34 hitches over 33 ms, mean solver
  2.70 ms. Previous retained mean/p95 were 14.70/30.64 ms. No claim of a
  performance improvement; frame and solver budgets still fail. No other
  engine instance or build ran during the measurement.

### Current geometry survey / next work

Six requested stations from 300 to 350 m completed with no unreachable stations.
All sampled raft supports were wet, ungrounded, and had 13.9–16.9 cm floor
freeboard. Three station sweeps reported lateral tilts of 0.78–0.92 m across
12 m. The largest sampled downstream drop was 0.92 m per 5 m. At the requested
340 m stop the drifting raft was actually at 342.48 m, lateral -3.66 m. The old
survey printed +53 cm clearance, but subsequent code inspection found that it
mixed the fixed terrain location with the drifting raft's support height.
That clearance is invalid; the corrected fixed-coordinate survey below supersedes it.

Next: inspect fixed-coordinate bathymetry/terrain alignment, then replace broad
trough-driven aeration with crest-localized generation and persistent downstream
foam; compare actual geometry and animated crest evolution again. Do not amplify
periodic whole-channel waves to conceal the missing hydraulic controls.

Follow-up evidence in the adjacent directory: shared-crest first/last frames,
full capture request logs, geometry survey log, numeric test log, and performance
JSON. The full 48-frame series remain in `unreal/Saved/Screenshots/` under
`chilko_crest_serial_{old,shared}_340_*.png`.

## Follow-up: linear water data and crest-local foam

Found a shared rendering-data bug in the installed UE 5.8 implementation:
`CreateMeshSection_LinearColor` defaults to **no** sRGB conversion, but
`UpdateMeshSection_LinearColor` defaults to conversion. Our R/G/B channels carry
foam/depth/speed, not display colors. All six update call sites in the water
surface actor now explicitly disable conversion, including interpolated live
water, recenter updates, the carrier and ripple sections. This applies to all
river scenes; it is not a change to physical solver values. Other scenes still
need visual recalibration/review with the corrected channels.

Unreal `RaftSim.P2.WaterDataLinearEncoding` passed: it creates a real procedural
mesh, demonstrates that the default update encodes 0.05 foam to more than four
times its original byte value, then verifies repeated explicit-linear updates
preserve every data channel. This establishes the encoding defect/fix, not a
complete explanation of every historical flash or stripe. The current images
still contain excessive optical mottling and do not prove photorealism.

Chilko-only `raftsim.ChilkoCrestFoam` now defaults to 1. Positive hydraulic relief
and the eased accepted breaking crests generate new crest foam; negative relief
and the old raw-detection tail's unconditional 0.38 decay term no longer do.
Existing plunge-pocket/boil/wake sources, foam advection and attack/release remain.
Setting this CVar to 0 restores the old foam sources for an isolated comparison.
The source change alone produced only a modest visual difference before the
encoding correction. The comparison probe with `HydraulicFoamIntensity 0` was
temporary and is **not** the retained state.

Corrected terrain sampling compares water and terrain at each requested fixed
centreline coordinate, rather than mixing fixed terrain with drifting support:

| Station (m) | Terrain Z (cm) | Solver bed Z (cm) | Water clearance (cm) |
| --- | ---: | ---: | ---: |
| 300 | -107 | -105 | 115 |
| 310 | -124 | -125 | 142 |
| 320 | -218 | -215 | 209 |
| 330 | -200 | -201 | 162 |
| 340 | -130 | -129 | 94 |
| 350 | -329 | -327 | 142 |

Thus the current six sampled centreline locations are not buried. This is not
a whole-shoreline clearance survey. No terrain or hydraulic assets were changed.

Actual post-fix captures: 16 frames at requested 300 m and four each at 24/340 m;
all expected files exist. Inspected first/last rapid frames and approach/lateral
views. The approach has no broad generated froth; the rapid has more open-water
gaps, but large wave faces remain weak and the spray is still puff-like. No
photoreal acceptance or continuous-video validation is claimed. Next work should
address physical-scale crest geometry and roller/spray shape, not reintroduce
gamma-amplified foam to hide the remaining gaps.

Win64 build and 30 focused plain Python tests passed. Matched offscreen performance:
1,292 frames; mean wall 15.49 ms (64.6 FPS), p95 33.49 ms, max 40.49 ms;
70 frames exceeded 33 ms. Mean solver step 2.76 ms. Six aerosol and six roller
sites remained active. This is slightly slower than the previous single sample,
not a demonstrated optimization; both frame and solver budgets still fail.
No other engine process/build ran during the performance sample.

Evidence: `WaterDataLinearEncoding.log`, `ChilkoFixedGeometry.log`,
`chilko-performance-linear-data.json`, and `chilko_linear_*.png` in the adjacent
directory. Full capture sequences/logs also remain under `unreal/Saved/`.

## Follow-up: crest-owned spray

Chilko's rapid Niagara sources now require nonzero persistent crest presentation
weight and a wet support sample. Their centre is sampled on the same supported
surface, with 3 cm roller/droplet and 6 cm aerosol offsets instead of fixed
32/60/38 cm lifts. Spawn density follows eased ownership; weak-site component
scale requests are reduced. The small sideways launch bias is keyed to the
persistent shape seed, not camera-distance pool order. Other scenes retain the
old behavior. `raftsim.ChilkoCrestSpray 0` restores the baseline for comparison.

Actual A/B captures at requested 300 m show fewer detached bank-side plumes and
more localized spray. Sixteen candidate frames and eight final 340 m frames were
produced; inspected the first/last 300 m frames and a 340 m lateral view. Eight
Chilko source guards and the Win64 build passed. This is not full-motion or
photoreal acceptance. No Niagara assets or physical wave shapes were edited.

Matched offscreen sample, before the final sideways-seed-only change: 1,347
frames, mean wall 14.86 ms (67.3 FPS), p95 32.10 ms, max 35.90 ms, 29 hitches
over 33 ms, mean solver 2.66 ms. Three aerosol/roller sites were active instead
of six because particles now follow the three-site geometry ownership budget.
This deliberately reduces detached emission; it is not an equal-work performance
optimization. Frame and solver budgets still fail. No concurrent engine/build.

Remaining: the source planes are authored in emitter-local coordinates while
the emitter pitches upward to launch spray. Consequently their spatial footprint
also tilts above/below the water. Separate source-plane orientation from launch
direction next; merely lowering the source centre does not fully correct that.
Large supported crest shapes, fine droplet/film silhouettes and the overly even
surface foam also remain unresolved. New evidence uses `chilko_spray_*` images
and `chilko-performance-owned-spray.json` in the adjacent directory.

## Follow-up: independent spray source orientation

The three rapid Niagara systems now expose a quaternion source-plane rotation.
For Chilko only, runtime counter-rotates the emitter's pitched launch transform
so the source strip stays horizontal, with its long axis across flow. Launch
velocity keeps its original direction. Other scenes receive identity rotation.
`raftsim.ChilkoSprayPlane 0` restores the tilted-source baseline independently of
crest ownership. A scoped asset upgrade preserves existing particle modules and
materials; the normal authoring path also retains this binding.

The Win64 build and all 32 plain presentation guards passed. The engine geometry
test checks 25 heading/pitch combinations, strip-corner elevations, unchanged
launch direction, and zero-direction safety. The saved-asset binding test checks
all three systems. The initial NullRHI test could not establish GPU readiness
and failed that assertion; both tests passed in a fresh rendering-enabled process
loading the saved assets. Both logs are retained, not just the passing one.

Produced all 16 frames for each tilted/level 300 m run. Inspected frame 003 in
both, and level frame 015. This corrects the spatial emission footprint, but the
visible difference in these views is small; isolated puffs and nearly uniform
foamy detail remain. These are screenshot sequences, not real-time playback or
deterministic, time-matched particle replays. A horizontal strip is also not a
fully surface-conforming source over a sloped or curved crest.

The next major issue is hydraulic geometry scale, not particle orientation:
the shared profile uses `0.22 m * Intensity`, and this run logged strongest
interior intensity 0.179 on initial refresh (roughly 4 cm before further fading).
The stronger rejected sites were shore-adjacent. Enlarging every wave or removing
wet-bank rejection would hide that distinction and risk the earlier shore blobs.
Investigate local hydraulic placement and depth/velocity-derived crest scale;
keep both raft support and visible relief on the same profile. The OARS/Chilko
footage comparison remains a failure for broad wave faces and foam distribution.

Performance (sequential 20 s samples, 12 s warmup, same offscreen 1280x720
protocol and three aerosol/roller sites):

| Source orientation | Frames | Mean wall ms | p95 wall ms | Max ms | >33 ms frames | Mean solver ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Level, first run | 1113 | 17.99 | 34.39 | 41.98 | 129 | 2.80 |
| Tilted, same new binary/assets | 1330 | 15.04 | 31.81 | 39.24 | 31 | 2.66 |
| Level, repeat | 1311 | 15.26 | 32.57 | 39.03 | 45 | 2.68 |

The first level run was slower; the repeat was close to the tilted baseline.
These short runs show substantial variability, not a proven speedup or a clean
no-regression qualification. All still fail frame and solver budgets. No
concurrent engine or build ran. Keep the physically corrected orientation, but
do not call performance accepted. JSON evidence uses `chilko-performance-*-spray*`;
selected actual images use `chilko_spray_level_300_*` and
`chilko_spray_tilted_300_003.png` in the adjacent directory.

## Follow-up: depth-scaled crest reconstruction

Chilko now reconstructs unresolved first-wave height from upstream depth/Froude,
subtracting the positive surface rise already in the solver. The undular estimate
uses USACE EM 1110-2-1601 Eq. 4-5; it blends toward a conjugate-depth-rise scale
above the undular regime. Source: [USACE hydraulic design manual, section 4-3](https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1601.pdf).
The blend, 0.8-depth/1.2 m amplitude caps, 2–7 m face lengths and asymmetric
curved crest/toe/tail profiles are bounded presentation approximations, not
measured Chilko geometry or a new fluid simulation. The interpreted 2 m cook
remains unchanged. In particular, the earlier initial intensity 0.179 included
spawn fading; it must not be read as a direct steady upstream Froude measurement.

Persistent sites ease these dimensions, fade height with lifetime and ownership,
and supply the same field to raft support and the single visible carrier. The
existing wet/interior rejection and shoreline taper remain. Other scenes retain
the legacy profile. `raftsim.ChilkoHydraulicCrestScale 0` restores it in Chilko.
Raised wave faces no longer automatically create crest foam: fresh foam is
restricted to the narrow top and an eased spilling fraction starting at upstream
Fr 1.28. Existing transported foam, boulder wakes and other aeration sources
remain, so this does not eliminate all excessive whiteness.

Two Win64 builds succeeded. Both engine tests (`HydraulicCrestScale` and
`SharedBreakingRelief`) passed after the final spilling change. Coverage includes
resolved-rise subtraction, dry/subcritical rejection, local/global bounds,
continuous finite support, ownership fading, legacy behavior, and green
upstream faces/nonspilling crests/toes. All 32 existing plain presentation guards
also passed. These checks do not establish visual realism or exact agreement
between off-vertex analytic support and triangulated render geometry.

Final captures: all 16 requested 300 m frames and all eight 340 m frames were
written; inspected 300 m frames 003/015 and 340 m frame 003. The initial
strongest site's new eased height was 0.080 m with a 2 m face length, versus
about 0.039 m from the previous fixed-lift calculation before ownership/taper.
Comparison with the earlier 340 m image also shows that a broad dark foreground
face already existed there. Therefore the new image cannot be credited as a
wholly new large wave: the visible improvement is modest and these drifting
camera sequences are not controlled, time-matched A/B replays. Against the real
Chilko references, the water still lacks distinct large breaking faces, foam is
overly mottled, and spray reads as upright puffs. No photoreal acceptance.

The final matched-protocol performance sample recorded 1,299 frames: mean wall
15.41 ms (64.9 FPS), p95 32.51 ms, max 37.43 ms, 45 frames over 33 ms, and mean
solver step 2.70 ms. Three aerosol and three roller sites remained active.
This is close to the preceding level-source repeat (15.26/32.57 ms mean/p95),
not a demonstrated speedup. Frame and solver budgets still fail. No concurrent
engine or build ran. Final evidence is `chilko_spilling_crests_*`,
`ChilkoHydraulicCrestSpillTests.log`, and
`chilko-performance-hydraulic-crests.json` in the adjacent directory.

## Follow-up: gameplay was overriding Chilko's foam calibration

The saved current-water instance has breakup gain 0.58, but the shared
single-surface initialization replaced it with 3.0. This clamped the foam lace
toward solid white and hid wave faces. Saved-material tests did not cover that
runtime override. A temporary coverage-gain reduction from 4.0 to 1.2 had little
visual effect; restoring the breakup gain instead produced a clear reduction
in the white blanket. The fix preserves the inherited breakup gain for Chilko
only. Other river behavior, hydraulic foam sources, flow, geometry and assets
are unchanged in this follow-up.

`RaftSim.WaterMaterialProbe` now accepts an optional final `delay=<seconds>` and
logs section visibility, wet-vertex foam counts and the effective foam gains.
At 9.001 game seconds, with no material override, the actual visible
`LiveVolumeCoreMesh` reported intensity 0.9, coverage gain 4.0, breakup gain
0.58 and core gain 1.8. Its 6,395 alpha-qualified vertices included 858 above
0.2 foam and 155 above 0.5. Those are mesh samples, not screen-pixel coverage.
The similarly named `SurfaceMesh` sections were hidden; their shader parameter
lookup is not evidence for the displayed water. The build and 33 plain
presentation guards passed.

The no-override captures produced all 12 requested 300 m and eight 340 m frames;
inspected frame 003 at both positions. The second settled probe also confirmed
0.58 on the visible carrier. Dark wave faces are no longer covered by the same
opaque-looking lace, but the reference's dense bright crest caps are now clearly
underrepresented: restoring the authored response is not final foam calibration.
Next, separate sparse transported coverage from dense fresh crest foam in the
material response; do not reinstate a global boost that whitens both. Upright
spray puffs and insufficiently distinct breaking geometry remain. This is a
verified override fix, not scene acceptance or full-motion validation.

Final offscreen sample, without probes/screenshots: 1,317 frames, mean wall
15.19 ms (65.8 FPS), p95 32.31 ms, max 35.16 ms, 48 frames over 33 ms, mean
solver 2.67 ms. Frame and solver budgets still fail; no speedup claimed. No
concurrent engine/build. Evidence: `chilko_foam_runtimefix_*`,
`ChilkoFoamRuntimeFix*.log`, and `chilko-performance-foam-runtimefix.json`.

## Follow-up: density-aware foam colour

The Chilko current parent now preserves sparse transported foam's existing
response but progressively closes the same advected lace at high aeration.
Dense interiors can approach opaque white without boosting all weak foam.
The response begins at conditioned aeration 0.28 and reaches its dense regime
at 0.72. Its threshold has pixel-footprint filtering and a 0.06 minimum width;
increasing aeration cannot erase existing coverage. These are visual calibration
choices, not a measured bubble-volume model. `ChilkoDenseFoamBlend=0` restores
the previous colour response for in-process A/B comparison.

The graph change is Chilko-only, targets hydraulic foam rather than the later
drift-fleck tint, and introduces no new texture, panner or water surface. The
scoped refresh re-saved the current parent, its live instance and its existing
first-party flow-normal/foam-lace dependencies. Initial validation caught the
wrong shared-colour branch and a default unbound custom input; both were fixed.
The final build, 34 plain guards, and the rendering-enabled
`RaftSim.M9.FChilkoLavaCanyonWater` authoring/graph test passed. Repeated authoring
keeps one connected node with four bound inputs. That test reauthors the asset;
the subsequent game captures load the saved result in separate processes.

All 12 baseline and 12 candidate 300 m frames, plus eight candidate 340 m frames,
were written. Inspected baseline/candidate frame 003, candidate 300 m frame 011,
and candidate 340 m frame 003. Dense caps are visibly brighter and localized
near the 300 m feature; the downstream view does not regain the white blanket.
The OARS/Chilko reference still has more irregular, volumetric breaking crests:
these caps remain too rounded/flat and the spray still resembles upright puffs.
These are drifting screenshot sequences, not deterministic particle replays or
full-motion validation. No scene acceptance.

Remaining coupling issue: the new response currently changes foam colour only.
Roughness and transmission still consume the earlier foam mask. Align their
dense-foam response next so bright caps do not read as glossy paint. Geometry,
spray trajectories, continuous rapid structure and frame-time spikes also remain.

Final offscreen performance sample: 1,314 frames, mean wall 15.22 ms (65.7 FPS),
p95 30.72 ms, max 35.19 ms, 48 frames over 33 ms, mean solver 2.64 ms. Mean
frame time is essentially unchanged from the prior 15.19 ms sample; the lower
p95 in one short run is not a proven optimization. Frame/solver budgets still
fail. No concurrent engine/build. Evidence: `chilko_density_*`,
`ChilkoDensityFoamMonotonic.log`, and `chilko-performance-density-foam.json`.

## Follow-up: dense foam optical consistency

Chilko's dense coverage now also drives the three existing optical consumers:
foam roughness, water opacity and aerated volume scattering. The graph migration
checks all three connections and preserves its legacy input without creating a
cycle. WPO, shoreline opacity-mask coverage, physical depth and solver state are
untouched. `ChilkoDenseFoamOpticsBlend=0` restores the preceding colour-only
behavior; `ChilkoDenseFoamBlend=0` still disables density enhancement itself.
Other river parents are not migrated by this change.

Build and all 35 plain guards passed. The rendering-enabled Chilko authoring
test passed, including the helper's all-three-consumers requirement. Fresh game
processes loaded the saved material for 12-frame off/on sequences at 300 m.
Inspected off/on frame 003 and on frame 011. No material compilation failure
appeared. The optical difference is subtle in these drifting views, not a
demonstration of photoreal foam; caps remain rounded/flat and spray still looks
like fountains. These are not synchronized particle replays or full-motion
acceptance. Scoped refresh re-saved the existing Chilko material dependencies.

Performance: 1,331 frames, mean wall 15.04 ms (66.5 FPS), p95 32.68 ms, max
37.53 ms, 54 frames over 33 ms, mean solver 2.71 ms. No concurrent engine/build.
Frame and solver budgets still fail; variation relative to the prior short
sample is not a demonstrated improvement. Evidence: `chilko_optics_*`,
`ChilkoDensityOpticsAuthor.log`, and `chilko-performance-density-optics.json`.

Next concrete spray issue found in the current authored profile: rapid roller
particles use only 260 cm/s² downward gravity, launch at 140–320 cm/s, live
0.50–0.96 s, and use 40–70 cm-long velocity-aligned sprites. At steep launch
angles, many can vanish before falling back, and their large elongated cards
read as upright plumes. Correct the airborne trajectory/scale in a Chilko-scoped
variant and compare actual animation; do not simply hide all spray.

## Follow-up: Chilko-only ballistic spray variants

`RaftSim.CreateChilkoBallisticSpray` now duplicates the existing roller and
crest spray into `/Game/RaftSim/VFX/Water/Chilko/`. Shared river effects are not
modified. Chilko gameplay selects the pair together; missing assets retain the
legacy pair. `-RaftSimChilkoLegacySpray` restores the old pair for comparison.
The existing Water directory cook rule covers the new subdirectory, but a
packaged build has not been tested.

Both variants use downward gravity of 980.665 cm/s² and unaligned, compact
sprites. Roller speed is 120–260 cm/s, lifetime 0.65–1.0 s, and size 6×7 to
14×18 cm. Crest spray is 180–380 cm/s, 0.85–1.15 s, and 2×3 to 6×10 cm.
The minimum lifetimes exceed the vertical ballistic return time at maximum
launch speed (ignoring drag); this is a configuration check, not tracked-particle
motion evidence. Source-plane correction, spawn controls, materials and drag
are retained. The aerosol effect remains unchanged. There is no new fluid
collision or droplet-to-water feedback simulation.

Build passed. All 36 plain presentation guards passed. The rendered
`RaftSim.M5.ChilkoBallisticSpray` test passed both after authoring and in a
separate reload-only process. Checks cover isolated emitters, preserved source
gravity, variant gravity/lifetime/size, spawn schedule count, source quaternion,
renderer alignment and readiness. The test does not compare every spawn field.
Authoring saved both variants, and fresh gameplay logged their selection.

Captured all 12 baseline and 12 candidate frames at station 300 m. Inspected
baseline 003 and candidate 003/011. Oversized crest spray is reduced, but some
wispy upright plumes remain. The hidden fallback card pools are not the active
render path when Niagara is ready; identify the remaining visible emitter or
atlas contribution before changing it. These are drifting, unsynchronized
captures, not a deterministic replay or real-time animation acceptance test.

Against the previously inspected OARS Chilko photos and actual White Mile
footage, broad dark faces and localized white caps are present, but the caps
still read as rounded surface patches and the rapid is insufficiently continuous.
This is a limited spray improvement, not photorealistic acceptance.

Performance: 1,311 frames; mean wall 15.26 ms (65.5 FPS), p95 32.59 ms, max
40.05 ms, 52 frames over 33 ms, mean solver 2.67 ms. Frame and solver budgets
still fail. No concurrent engine/build. This short offscreen diagnostic shows
no demonstrated performance improvement. Evidence: `chilko_ballistic_*`,
`ChilkoBallisticSprayAuthor.log`, `ChilkoBallisticSprayReload.log`, and
`chilko-performance-ballistic-spray.json` in the adjacent evidence directory.

Chilko remains open. Next rotate to Troublemaker for a scene-specific pass;
do not propagate these spray choices to other rivers without their own visual
comparison. Returning Chilko work should prioritize sustained rapid structure,
remaining detached plumes, actual motion evidence and game-thread spikes rather
than further small optical parameter adjustments alone.
