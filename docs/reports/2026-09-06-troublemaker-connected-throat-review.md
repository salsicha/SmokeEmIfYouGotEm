# Troublemaker: bank-connected throat and honest motion capture

Status: **experimental, not photorealistic, not promoted to production**.
Continues the [previous precision/hydraulics review](2026-09-05-troublemaker-water-precision-review.md).
The all-river goal remains unchanged; no river scene is accepted.

## Bank connectivity change

The prior 12 m interpreted throat raised only originally wet cells. At its
central section roughly 19% of flow bypassed those raised islands through low
ground beside them. `bank_connected_throat()` is a distinct, opt-in variant
(`--bank-connected-shoulders`, identity `bank_connected_v1`). It ties the raised
shoulders into high terrain using a crest 0.8 m above the original **wet-channel**
median stage. It does not use dry-cell eta as the reference height.

The central sill/drop, high ground, lateral domain edges, and terrain outside
the local longitudinal envelope are unchanged. The new bed changes 7,995 cells,
including 4,399 originally dry cells; maximum lift is 2.13524 m, below its 4 m
guard. Initial section flux is preserved to numerical precision. This is an
interpreted authoring experiment, not surveyed bathymetry. The legacy generator
is unchanged so its saved frames remain reproducible. The isolated exporter
recognizes the new identity and rejects mismatched bed/variant combinations.

## Warm-up and rejected premature constant-flow attempts

A cold constant-Q start was rejected at time zero, row 40, h=0.052366 m,
u=0.760668 m/s: the experimental inlet requires a subcritical characteristic.
After 96 s of stage-boundary warm-up, a second constant-Q attempt was rejected
at t=0.36 s, row 116, h=0.040049 m, u=0.642248 m/s. Neither incomplete run is an
accepted result. **No C++ inlet guard or default was changed to force it through.**

The 96 s warm-up was still a strong startup transient: exact numerical west
inflow 51.4689 m³/s, east outward 3.05967, net storage +48.4092. Central throat
flow was only about 23.6 m³/s. Side-route flow was zero at central sections,
showing the geometric closure but not a settled hydraulic control.

An additional 192 s warm-up (96→288 s) completed in 699.276 wall seconds:

| Quantity at 288 s | Result |
| --- | ---: |
| Exact west numerical flux | 30.40461 m³/s |
| Exact east outward flux | 26.84467 m³/s |
| Net instantaneous storage | +3.55994 m³/s |
| Inlet median stage above prescribed stage | 0.11843 m |
| Hole-region median speed | 1.76408 m/s |
| Hole-region Froude p99 | 1.55792 |
| Hole-region supercritical wet fraction | 7.282% |
| Total volume | 22,249.459 m³ |

The stage-plus-velocity boundary still reduces actual inflow under backwater;
its metadata target 45.30695 m³/s is not an enforced flux. Therefore this is not
an equal-flow comparison with the earlier constant-Q trials.

The new `measure_throat_conveyance()` reports signed cell-centre section flux,
core flux and positive-downstream bypass fraction, with its width convention
explicit. At station 8358.5888 m, total Q is 29.20506 m³/s and flow outside ±9 m
is 0.12497 m³/s (0.428% of positive downstream flow). At 8362.5888 m it is
0.10502 of 29.37480 m³/s (0.354%). Thus small fringe flow returns as stage rises,
but the former large side channels are substantially suppressed. Do not call
the bank completely impermeable or the state steady.

Evidence is in `images/2026-09-06-troublemaker-water`: the two
`hydraulic-connected12-stage*.json` and `boundary-connected12-stage*.json` files.
The 288 s source is exported only to `tmp/troublemaker-review-connected12-stage288`.
The game uses its normal cropped first-order evolution after loading that state;
offline and live boundary conditions are not claimed identical.

## Actual scene review

Captured the FullReach map at explicit focus station 8360 m, lateral −1.5 m,
with the transient terrain correction, spatial breaking review and ballistic
spray enabled. The shoulders read as connected banks rather than separate
islands. However, the water remains a broad glossy sheet wrapping the exposed
rock, with sparse spray and insufficient piled white foam. Compare
`connected12-stage288-hole.png` with the user's real-whitewater photo
`codex-clipboard-d8abf384-5a0e-44a3-8de0-1baee54963ed.png`: the reference has
dense irregular white crests, dark steep faces, and much stronger foam volume.
Neither the new channel nor its low-flow imagery is accepted as realistic.

## Recording timing correction

The existing built-in MP4 recorder assigned timestamps as `sourceFrameCount/30`.
At 10 actual FPS this compressed ten seconds of motion into about three seconds,
invalidating animation-speed comparisons. Frames now carry monotonic request
timestamps through asynchronous readback; the previous frame's sample duration
is the interval to the next request. Final readbacks are drained after shutdown.
The source-frame count increments only after a successful encoder write.

The first live test revealed that `FApp::GetCurrentTime()` was stale during
blocking encoder initialization, creating a long first-frame hold. The corrected
implementation uses `FPlatformTime::Seconds()` at start, capture and stop.
Both versions were actually built and tested; the initial clip is retained in
`tmp/troublemaker-connected12-recorder10`, not silently replaced.

Corrected live test: deliberate `t.MaxFPS 10`, 1280×720, record toggles scheduled
at world time 11 and 21 s, with two still screenshots outside the main recording
interval. Log: `images/2026-09-05-troublemaker-water/TroublemakerConnected12Recorder10Clock.log`.
96 successful source frames cover 9.641 s according to the recorder. The MP4
contains 289 samples covering **9.6333 s**, versus **3.2 s** under the old
source-count/30 rule. The encoder repeats source frames to output a nominal 30 Hz
track; that is not 30 FPS gameplay or extra simulated motion. The frame table is
inspected by `audit_mp4_timing.py`, not inferred from a file label.

Corrected clip: `images/2026-09-06-troublemaker-water/connected12-stage288-recorder10.mp4`.
Timing record: `recorder10-clock-timing.json`. The selected PNG above is a separate
game capture from the first run, not a claimed decoded frame from the corrected
clip. No new isolated performance result is claimed.

Interactive playback review did not complete: browser integration reported Chrome
unavailable; the computer-use skill's native Chrome inspection then hit an app-
approval timeout. No alternate method bypassed that approval, and no continuous
playback judgment is claimed. The local clip was queued in the task file viewer.
Container timing and still-image review do not establish photorealistic animation.

## Verification and remaining work

Development Editor build succeeds. 70 plain scene, export, hydraulics, capture
and MP4-timing checks pass; `git diff --check` passes. These tests do not accept
the water's appearance. No shipping data or material defaults were promoted.
The fixed-Q continuation from the longer 288 s warm-up completed, as detailed
below. A stronger coherent roller, matched lighting/foam response, proper
spray return, shoreline quality and playable performance remain unresolved.

## Constant-discharge continuation at 384 s

The 96 s continuation from the 288 s stage warm-up completed without a solver
failure (462.02 s offline wall time). Earlier cold and short-warm-up failures
remain recorded; no incoming-characteristic safety guard was weakened.
The exact west inflow is now 45.30695 m³/s, east outward flux is 33.08053 m³/s,
and instantaneous net storage is +12.22642 m³/s. Total volume is 23,784.754 m³;
inlet median stage is 0.23527 m above the prescribed reference. Hole-region
median speed rises to about 1.95 m/s and supercritical wet fraction to about 9.5%.

This is **not settled**: the last four samples fail all three convergence
screens (section flux, storage and stage stability). Maximum section discrepancy
is 35.36% of target and maximum interval storage is 37.32% of target. At stations
8358.5888 and 8362.5888 m, positive downstream flow outside ±9 m has grown to
3.024% and 2.681%, respectively. The shoulders reduce the old bypass but do not
eliminate it under rising head. Do not compare those fractions as if the legacy
and new experiments had identical flows and elapsed time.

The exported field is review-only at `tmp/troublemaker-review-connected12-fixedQ384`.
Evidence: `hydraulic-connected12-fixedQ384.json`,
`boundary-connected12-fixedQ384.json`, and `convergence-connected12-fixedQ384.json`
in this report's September 6 image directory.

### Actual fixed-camera image and recording

The FullReach game loaded that export with the same transient terrain, spatial
breaking and ballistic spray flags. Capture focus remains station 8360 m,
lateral −1.5 m. Both logged camera locations are identical. The raft advances
from station 8372.715 to 8373.804 m, independently of the fixed camera.
`connected12-fixedQ384-hole.png` is the second direct game screenshot, not a
decoded video frame. The drop is visibly three-dimensional, but still reads as
a glossy continuous sheet draping an exposed rock. Fine white flecks and a
broad bright reflection do not resemble the dense irregular foam crests and
dark steep wave faces of the user's real-whitewater reference. Steep smooth
shoulder banks also look authored rather than natural. **Visual acceptance fails.**

`connected12-fixedQ384.mp4` contains 237 successfully written source frames
over 9.641 s according to the recorder. Its independently parsed sample table
covers 9.6333 s, rather than the 7.9 s produced by the previous source-count/30
timing rule. The encoder outputs 289 samples at nominal 30 Hz by repeating
frames; this does not establish 30 FPS gameplay. This run has no artificial FPS
cap, but recording overhead and the short interval make it unsuitable as an
isolated performance benchmark. Interactive playback inspection remains
unverified after the app-approval timeout described above.

Next work must address the missing irregular crest/roller volume and its
shading, not merely increase foam brightness. Further settling is needed before
using this hydraulic candidate for a steady-flow comparison. No shipping scene
or material defaults are promoted and no river is accepted as photorealistic.

## Displacement-normal experiments

The next continuation made concrete progress through two built and rendered
normal experiments, not another hydraulic recook. The preceding continuation
also counts as progress: it completed the constant-Q solve, captured it and
independently verified recording duration. The goal remains active.

The saved local-fluid material adds vertical WPO but its normal graph does not
derive a matching slope from that function. `create_displacement_normal_review.py`
duplicates the current parent into isolated `/Game/RaftSim/Rendering/Review`
assets. The source material, scene assets, hydraulics, mesh and foam parameters
are unchanged. Both variants rotate the existing smooth/ripple normal rather
than discarding it. Camera-relative positions avoid subtracting large world
coordinates. Degenerate and nearly antiparallel faces fall back safely.

1. `M_RaftSim_DisplacementNormalReview`, enabled only by
   `-RaftSimDisplacementNormalReview`, computes the relative face rotation from
   pixel derivatives of pre/post-WPO position. Actual capture shows large
   triangular highlights across the rapid: the coarse displaced triangles
   become visible. **Reject this variant for production.** Evidence:
   `displacement_normal_on.png` and `DisplacementNormalOn.log`.
2. `M_RaftSim_SmoothDisplacementNormalReview`, enabled only by
   `-RaftSimSmoothDisplacementNormalReview`, evaluates the original local-fluid
   function three times per active vertex (centre and two 15 cm offsets), then
   interpolates its two-component slope to the pixel shader. The original
   custom expression is duplicated with its existing input connections, so it
   uses the same UV rebasing, flow integral, wave clock, amplitude and gates.
   Extra function evaluation does not move into the pixel shader. Foam, depth
   and window inputs are held constant inside the finite difference: their
   spatial gradients are not corrected. This is a bounded local-fluid shading
   approximation, not exact normals for every displacement term or full fluid
   simulation. Live stills remove the prominent facets from variant 1, but the
   broad glossy sheet and lack of thick irregular breaking crests remain.
   **No photorealism acceptance or production promotion.** Evidence:
   `smooth_displacement_normal_on.png`, `SmoothDisplacementNormalOn.log`,
   `smooth-normal-capture-audit.json`.

Both captures use the 384 s constant-Q review field and the same explicit
station/lateral camera preset. Within the smooth run the camera is exactly
fixed over 11.998 s and the two PNGs differ. Between runs the camera height
differs slightly with sampled water level and the live simulation is not
lockstep; do not attribute every changed pixel to normals. These sampled stills
do not establish motion quality. The user's real-whitewater reference was
viewed again: its dense irregular crest foam, dark steep faces and broken
surface are still substantially unlike either candidate.

Two Python API wiring failures preceded the first successful material save;
one unconnected advanced-pin lookup failure preceded the smooth material save.
The failed logs are retained. The corrected generation commandlets succeeded;
both game runs logged the expected material, a single water surface and no
material shader compile failure. Existing unrelated experimental Toolset Python
startup errors remain in game logs, so this is not a claim of error-free logs.

### Matched-setup performance diagnostics

Sequential runs, no simultaneous solver/editor, 12 s warm-up plus 20 s
measurement, 1280×720 at saved 87% screen percentage, normal raft-follow camera,
same 384 s review data and terrain/breaking/spray flags. No screenshots or
recording during measurement. Development/offscreen engineering diagnostics,
not packaged or focused-window release qualification; live trajectories can
diverge, and one run per variant does not establish statistical equivalence.

| Measurement | Current parent | Smooth-normal review |
| --- | ---: | ---: |
| Samples | 620 | 617 |
| Mean wall frame | 32.261 ms | 32.438 ms |
| P95 wall frame | 44.031 ms | 43.461 ms |
| Mean GPU | 10.886 ms | 11.186 ms |
| P95 GPU | 12.020 ms | 12.111 ms |
| Mean solver step | 10.341 ms | 10.290 ms |

Evidence: `normal-review-baseline-performance.json`,
`normal-review-smooth-performance.json` and corresponding `Normal*Performance.log`.
The additional mean GPU cost observed is about 0.30 ms; no speedup is claimed.
Both runs fail the 16.67 ms frame and 1.6 ms solver budgets. Game-thread/solver
cost remains a major obstacle independent of this normal correction.

Development Editor build succeeds; 73 plain checks pass including three new
normal-math/isolation checks. These checks validate rotation identities and
review scoping, not shader execution, visual realism or performance. The next
large visual task remains coherent breaking/roller geometry and aerated volume,
not further brightening the glossy sheet. Mean-flow settling, natural banks,
continuous animation review and performance remain unfinished.

## Live crest-height budget audit

The following continuation is progress: it added and ran a one-shot live
diagnostic, compared two actual surface-filter captures, and started the next
constant-flow settling continuation. The preceding normal-review turn also
made progress through built shaders, actual captures and paired performance
measurements. No scene acceptance has changed.

`-RaftSimBreakingHeightAudit` logs detected transitions once after world time
10 s, including upstream depth/Froude, downstream Froude, raw and optical rises,
the extra height calculated from each rise, and geometric eligibility. It does
not change a physical value. `audit_breaking_height.py` validates and summarizes
the snapshot. The rows precede deduplication and persistent-site weighting:
they are **not** counts of independent waves or final rendered crest heights.

At stations 8355–8365 m on the 384 s candidate, the 16-pass run has 27 eligible
candidate transitions. Twenty-three positive raw rises become negative optical
rises. At station 8361 m, lateral +1.5 m, the raw rise is +0.2990 m and the
optical rise is −0.0926 m. Deducting the former from the crest-height budget
produces 0.3806 m extra relief, versus 0.6796 m using the latter. This confirms
one suppression mechanism, but does not justify adding 0.299 m blindly: raft
support still samples a different, one-pass base and could then double-count it.

The core's upstream depths are roughly 0.56–0.95 m and Froude numbers roughly
1.2–1.55. Several candidates already calculate 0.45–0.65 m extra relief, limited
by the depth cap; for these, changing the rise argument alone has little effect.
The old first-refresh diagnostic reporting a strongest 0.01 m crest was not a
measurement of the fully evolved central hole. Do not use it to claim that all
crest heights are only centimetres.

The one-pass optical ablation retains four-pass hydraulic source detection.
At its snapshot, 12 of 27 eligible transitions have reversed rises and the
maximum computed extra-height deficit is 0.2599 m. Both runs use the smooth
normal review, same source field, transient terrain and fixed-camera preset;
live trajectories/times differ slightly, so they are not exact state-identical
pixel comparisons. At 17 s the one-pass image preserves more of the wave face,
but both images still look like glossy ramps with fine white specks, not the
thick broken crests of the real-whitewater reference. Neither filter choice is
accepted or promoted. No new performance claim accompanies this ablation.

Evidence in the September 6 image directory:

- `BreakingHeightAudit.log`, `breaking-height-16-pass.json`, `breaking-height-16-pass.png`.
- `Connected12OnePass.log`, `breaking-height-1-pass.json`, `breaking-height-1-pass.png`.

Development Editor build succeeds, 75 plain checks pass and `git diff --check`
passes. Two new parser tests reject invalid/mixed snapshots and check that
erased rises are counted without pretending to measure final crest geometry.

### Next hydraulic continuation in progress

Started another 192 simulated seconds from the exact connected-bed 384 s frame,
at constant west discharge 45.3069545472 m³/s, with the same native solver and
safety guards. Output: `tmp/troublemaker-connected12-fixedQ576`. This does not
change production fields. Initial live handle: exec session 20926, native PID
20820, confirmed running after launch. This is a resumable job reference, not a
claim that it has completed or converged. Inspect that handle and current
process/output state before resuming; never restart just because observation
times out. Do not run UE capture/build/performance concurrently with this solve.

After completion, check exact boundary flux, storage and the convergence screen
before exporting or judging the new visual state. The main unresolved work is
still shared physical/rendered crest shape, breaking foam volume and animation,
shoreline quality and playable performance across every river.

## Completed 576 s continuation and first actual 3D liquid prototype

This continuation made progress: the same native job completed, its exact
boundary balance was audited, its review field was rendered in UE, and a new
offline Mantaflow prototype was built and inspected. No scene is accepted and
no production field or renderer default was promoted.

### Constant-Q 576 s result

Session 20926 completed successfully, using 1,325.94 wall seconds for the next
192 simulated seconds. The final volume is 25,475.712 m³. The exact west face
inflow is 45.30695 m³/s; east outflow is 40.48170 m³/s, with no north/south flux.
Net storage is still +4.82525 m³/s. This is an open-boundary filling problem;
the positive volume change is not by itself a conservation error.

All three convergence checks still fail. Across the final four samples, maximum
section discharge error is 12.86%, maximum interval storage/inflow is 13.71%,
and regional median stages change by up to 0.01311 m. Hole median speed is
1.748 m/s and the supercritical wet fraction is 10.0%. At stations 8358.5888
and 8362.5888 m, positive flux outside ±9 m is 7.36% and 6.71%, respectively:
the higher head has increased lateral bypass. Running longer has not simply
made the rapid stronger or sealed the shoulders.

The exact final field was exported into `tmp/troublemaker-review-connected12-fixedQ576`
and captured with the one-pass optical and smooth-displacement-normal reviews.
`connected12-fixedQ576.png` is an actual game capture at the fixed camera, not
a mockup. It shows visible green ridges and a depression, but still broad glare,
glossy ramps, fine white specks, and unnaturally smooth banks. It lacks the
thick, irregular broken crests in the previously inspected real-whitewater
photo. **Rejected as photorealistic.** Two stills do not validate animation.
No fresh performance comparison was made for this candidate.

The live height audit has 29 eligible pre-deduplication transitions at stations
8355–8365 m, 13 reversed rises, maximum computed extra-height deficit 0.3363 m,
and maximum raw extra relief 0.6797 m. These remain candidate calculations,
not final visible wave heights or evidence of full raft/render parity.

New evidence in the September 6 image folder:

- `Connected12FixedQ576.log`, `connected12-fixedQ576.png`.
- `connected12-fixedQ576-hydraulics.json`, `connected12-fixedQ576-boundary.json`,
  `connected12-fixedQ576-convergence.json`, `breaking-height-fixedQ576.json`.

### Isolated liquid feasibility test—not game integration

The installed Blender 5.2.0 LTS provides an actual Mantaflow liquid solver.
The prior V10 depth-bearing review was a procedural implicit-mesh cache, not a
liquid simulation; its closed underside thickness did not establish realistic
breaking-water shape. The new diagnostic is separate from that rejected asset.

`export_liquid_review_patch.py` validates the exact hydraulic frame and exports
an 11.5 × 8 m straightened patch from station 8355.0888 m, lateral −4 m.
It preserves the source bed, stage and horizontal velocities with an explicit
local elevation datum. Nominal sampled inlet discharge is 27.85390 m³/s for
this partial-width strip, **not** the entire river's 45.30695 m³/s. Actual
Mantaflow inlet discharge has not been measured. Source state is not settled.

`build_liquid_patch_review.py` builds an isolated 80-cell-longest-axis liquid
domain (approximately 0.144 m cells), exact source-bed collision, a banded
inlet and downstream removal volume. It bakes 144 frames at 30 Hz; these are
offline cached simulation frames, not a gameplay FPS result. Closed lateral
boundaries and the free outlet without prescribed tailwater are significant
approximations. No navigation, surveyed-layout, steady-state or seamless-loop
claim is made.

The first bake (`mantaflow80`) completed data, mesh and secondary-particle
caches. Actual opaque shape renders at frames 48, 96 and 144 were inspected:
a mostly smooth declining sheet with a conspicuous inlet-edge wall, not a
convincing breaking roller. The render deliberately omits secondary particles
and uses diagnostic opaque shading. Cached particle-array counts are not
visible foam counts or proof of foam quality. This prototype is rejected for
game integration.

Inspection exposed an initial-fill volume extending through the solid bed.
The second bake (`mantaflow80-bedfill`) initializes above the bed instead.
It completed in 143.99 seconds. Actual renders at frames 48 and 144 remain too
smooth; correcting the fill did not establish a realistic hole. The collider
was separately confirmed enabled, collision type, with top domain border open
and all other borders closed. The free outlet can draw down the downstream
pool; that boundary must be addressed before treating this as a faithful hole.

A geometry regression test also found ambiguous top/bottom quad triangulation.
The generator now uses matching explicit diagonals, and its closed outward-wound
surface preserves the interior bed and known test volume. A third bake,
`tmp/troublemaker-liquid-patch576/mantaflow80-velocitytiles`, adds 1 m-scale
piecewise initial velocities so the accelerating jet and slower runout are
not replaced by one uniform mean. It was launched as session 51553; inspect
that handle and its `bake-result.json` before resuming rather than restarting.
Its initial status here is in progress, not an accepted result.

`render_liquid_patch_review.py` additionally samples the actual evaluated upper
surface with downward rays. Whole closed-mesh thickness is deliberately not
reported as breaking-wave height. No Blender material, mesh cache or particle
system has been installed into the game. These experiments do not improve—or
measure—shipping performance. The next gates are correct boundary/state
coupling, a visibly broken surface and foam, temporal review, then bounded
game integration and measured performance.

The existing 75 plain checks plus three new liquid-export/geometry checks pass
(78 total). Tests cover manifold winding, interior bed preservation, volume,
invalid geometry, units/datum/flux, review-only flags, invalid inlet/bounds and
refusal to overwrite evidence. They do not establish visual realism.

### Spatial-velocity and tailwater tests completed

The third bake, session 51553, completed successfully in 152.95 seconds; it is
no longer running. Actual frames 24, 72 and 144 were inspected. At local centre
profile x ≈ 8.11 m the upper surface falls from 2.045 to 1.027 m relative to
the patch datum. At x ≈ 10.61 m it falls from 1.350 to 0.832 m. The transient
raised feature disappears into a mostly smooth descending sheet. This is
measured upper-surface drawdown, not inferred from total closed-mesh bounds.

An explicit `--tailwater-drain-depth 0.35` ablation replaces full-column
downstream removal with banded removal above the source outlet stage minus
0.35 m. It is an idealized reservoir control, **not** a validated characteristic
boundary or a guarantee of exact stage/discharge. It completed in 185.70 seconds
(session 5538). Its three actual renders and upper-surface measurements show
that the downstream pool is retained: at x ≈ 10.61 m, final centre-profile
surface is 1.729 m versus 0.832 m with free removal. However, the final surface
is still a smooth pool with low irregular relief, not a thick breaking roller.
At x ≈ 8.11 m the final surface is 1.760 m. The controlled-outlet test is also
**not accepted for game integration**. Retaining water level alone does not
establish correct discharge, velocities, breaking or foam.

The user's real-whitewater reference was viewed again directly during this
continuation (`codex-clipboard-d8abf384-5a0e-44a3-8de0-1baee54963ed.png`): thick
irregular white crests interrupt dark green faces, with dense froth rather
than the diagnostic's smooth sheet or the game's fine reflective speckles.
The exact rapid in that still is not independently verified. No continuous
reference/game animation comparison was completed in this continuation.

Compact evidence (input, bake status, measured surface profiles and final PNGs)
is preserved under `images/2026-09-06-troublemaker-water/liquid-prototype/`.
Raw caches remain under `tmp`; the first three alone consume approximately
15.4 GB. These unbounded secondary-particle caches are not viable shipping
assets as-is, and their particle-array lengths must not be presented as live
visible-particle counts. No caches were deleted or committed. Before another
expensive bake, measure actual 3D inlet/section flux and velocities and resolve
the boundary/mean-flow mismatch. More particle detail cannot fix a missing
hydraulic roller. Only then test a bounded surface/foam representation in the
game, inspect continuous animation, and measure performance.

All native/Blender jobs from this continuation have completed. No UE session,
solver or bake is intentionally left running. The goal is active and making
progress, not blocked; every river remains unaccepted. The current source adds
an early rejection of dry interior patches so it cannot build an inverted
closed water fill. The three liquid regression checks pass with that guard.
