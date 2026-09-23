# Reusable MUSCL stage storage

September 23, 2026. South Fork performance work; reconstruction remains unfinished.

The solver previously allocated and initialized primitive and half-slope vectors
for each immutable Runge–Kutta stage. It now leases calling-thread storage.
Every primitive member is still overwritten from the current stage, and all six
slopes are reset before reconstruction: dry cells and dry-neighbor directions
must not inherit old slopes. Nothing is retained as authoritative water state.
The original reconstruction, flux, boundary, friction and reduction expressions
are unchanged. There is no public solver-layout change.

Joined row workers borrow disjoint ranges. Simultaneous callers on different
threads have independent storage. Nested calls allocate an independent lease;
exceptions release the lease. Capacity, not numerical state, remains until the
calling thread exits. Retained storage scales with the largest grid seen on that
thread in each linked solver module (80 bytes per cell for these two vectors,
plus vector capacity overhead).
This is a memory-for-allocation tradeoff, not a reduction in resolution or cadence.

## Native qualification

Fresh baseline and candidate builds each pass all six native CTest cases.
Additional ownership tests cover nested and cross-thread calls, changing sizes,
resetting all slopes and exception recovery. Existing tests cover wet/dry state
replacement, three flux schemes, roughness, bed coupling, CFL subdivision,
serial/parallel evolution and Cartesian shared faces. The final candidate rerun
passes six cases in13.21 seconds. No acceptance limits were relaxed.

Two retained-input comparisons each run four alternating-order pairs of600 steps.
Every saved primitive, derived-field and dry-mask CSV matches byte-for-byte.
Candidate solve/capture time is lower in every pair:

| Retained input | Baseline median | Candidate median | Reduction |
| --- | ---: | ---: | ---: |
| Cartesian crop | 3.362215 s | 2.177495 s | 35.24% |
| Registered rapid | 3.284595 s | 2.097080 s | 36.15% |

These are component timings under the continuing cook workload, not game FPS.
The Cartesian recipe retains its earlier runtime-export identity limitation;
neither input proves whole-river geographic or hydraulic validity.

Baseline executable SHA256:
`3682381b2ebdad3131599995e5e0ffffcd6aa978028697f8ec3dcef00779db5c`.
Candidate executable SHA256:
`dc9903567056f4f3b72d2eb481397d3615afc70f53714fadc8c2965278331e16`.
Reports: `tmp/solver-stage-cartesian-pairs-v1-20260923/report.json` and
`tmp/solver-stage-registered-pairs-v1-20260923/report.json`.

## Normal runtime integration and limits

Two normal-start900-frame baseline runs completed before rebuilding. Their
process receipts confirm four solver lanes, D3D12,1280×720, modern CSV timing
and successful guarded suspension/resumption of the sole cook. No capture or
candidate flags were active. These are short first-pool windows, not rapid-at8330
or full-route acceptance. Independent audits use rows60–840 and scope offset1.
Baseline A mean26.310871ms/p9536.8774ms and B mean26.070925ms/p9535.3842ms
both fail the33.333333ms p95 budget. Reports:
`tmp/solver-stage-before-a-cost-v1-20260923.json` and
`tmp/solver-stage-before-b-cost-v1-20260923.json`.

The old archive, editor water DLL and standalone executable are preserved in
`tmp/solver-stage-game-baseline-v1-20260923`. The normal solver archive rebuilt
with SHA256 `63e9e59209d4cd4dc4c70f47e5f1c8fc64d8e903a86bcf9d967d0cb9f1d0365f`.
Editor and standalone builds are TERMINAL exit0 in session54658. Editor build
took1984.76 s and Game219.63 s. Existing C4701 coverage-test and C4305 damping
warnings remain; neither this nor a standalone target build is packaged-release
qualification. The checks below use the rebuilt normal editor-hosted game path;
no packaged execution is claimed.

A one-shot validation runner ran in session25650: PID3856, exact start
UTC2026-09-23T19:41:12.5454386Z. It held the original sequential build host's
handle (PID8340/start2026-09-23T19:24:37.8233062Z), checked both terminal build
successes and all seven native qualification hashes, then ran the Cartesian
engine prefix. Its intended cost/motion sequence stopped at the count check
described below. The existing profiling helper owns
identity-guarded cook suspension/resumption, including its error cleanup.
The runner never launches another build/cook and fails rather than overlapping
another active editor/compiler. Receipt:
`tmp/solver-stage-validation-runner-v1-20260923.json`; script:
`tmp/finish-solver-stage-validation-v1-20260923.ps1`.
The runner is now TERMINAL exit1 because its expected successful-test count was
four, but the actual prefix selects five tests. The retained engine report
`tmp/solver-stage-native-v1-20260923/index.json` has five successes, zero failures,
warnings, not-run or in-process tests. In addition to the four named tests, the
fifth is `CartesianStreamingActorFollowsBothAxes`; its signed XY handoffs pass.
All four originally required tests also pass. This is a runner expectation error,
not an engine failure; its failed receipt remains unchanged and the native tests
were not repeated. Cost/motion captures subsequently completed directly through
the same guarded helper, using the originally reserved labels. No runner remains.

The [runtime receipt](solver-stage-storage-runtime.json) retains test identities,
build/binary identities, process receipts, timing audits and decoded-motion hash.
The two separate post-change900-frame ordinary runs use the same normal scenario,
four lanes, resolution, D3D12, rows60–840 and confirmed timing offset1 as baseline.
No candidate, review-station or capture flags were used for cost measurement.

| Run | Mean frame ms | p95 frame ms | Elapsed FPS | Mean solver-step ms |
| --- | ---: | ---: | ---: | ---: |
| Before A |26.310871|36.8774|38.007104|4.362914|
| Before B |26.070925|35.3842|38.356906|4.350241|
| After A |25.956330|35.1858|38.526248|4.057597|
| After B |24.195281|33.4524|41.330373|3.779438|

Both post-change observations improve over both baselines, but these before/after
short windows do not isolate thermal, scheduling or trajectory variation. The
native alternating-pair exact-output result is separate evidence. **Every p95
still fails33.333333 ms.** This is not full-route, rapid-at8330, sustained or
packaged30FPS acceptance. Original CSV/process/audit artifacts remain retained.
The cook's CPU time was unchanged during both post-change cost captures; guard
suspend/resume statuses are zero. Its original binary/input remain untouched.

Separate normal-start motion exits0 with24 screenshots and a15.511 s recording.
Full decoding yields465 frames and15 adjacent exact repeats; encoded frame rate
is not game FPS. Inspected3,6,11 and13 s views show changing water patterns and
river progress from0.12 to0.14 km. Broad smooth water, coarse repeated canopy
and crew shading/fit limitations remain. This is not a breaking-water, whole-route
collision, shoreline-stability or surface-continuity acceptance. No new visible
detail is attributed to storage reuse. The three new gameplay logs have no
`Error:`, fatal-error, assertion-failed or Python-error matches; other warnings
and existing release failures remain.

The existing cook36692 remains on its original executable and unchanged input.
No source capture, material, terrain, collision, installed4950s field or nonlinear
activation changed. Reuse is integrated in the default runtime, not an opt-in
fixture. All build/test/capture jobs are terminal; only the original cook remains
live. Full-river reconstruction, realistic breaking/frothy water, collision,
shoreline/surface continuity, crew, sustained performance and release gates
remain open before South Fork or any queued river can be accepted.
