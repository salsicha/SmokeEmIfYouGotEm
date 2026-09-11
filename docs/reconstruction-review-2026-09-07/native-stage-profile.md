# Native water cost: measured stage-local reuse

The activity-memory engine run still averaged 9.000 ms in the live-water
solver, against the unchanged 1.6 ms budget. Inspection confirmed the timed
`LiveWindow->Step()` wrapper only calls `Solver->step()` and increments a
counter: the cost is not a hidden field export or texture upload in that wrapper.

## Reproducible isolation

`RAFTSIM_PROFILE_SOLVER` is a new **default-off CMake option**. Enabled builds
time finite-volume stepping, CFL evaluation, reconstruction, flux/update,
combination/friction, and derived-state recomputation. A thread-local summary
is emitted at thread exit. Timings are inclusive wall-clock durations; total
and nested stages must not be added together. Disabled builds compile out
the timers, storage, and reporting. No solver object layout changes.

`physics/scripts/profile_registered_solver.py` creates an isolated package
from the registered-rock scenario and the engine's exported float32 h/u/v/bed
fields, converted to native double storage. It preserves numerical and inlet
settings from the manifest. The benchmark is 600 steps at 1/60 s, not a
rendering workload or a claim about engine frame rate. Output directories
must be new; original captured data and prior reports are not overwritten.

The first fixture attempt failed before stepping because the NPZ depth field
was named `h` rather than the loader's `depth`. Corrected after inspecting the
loader. The failed report is retained under `native-stage-profile/`.

## Changes and results

The baseline attributes 27.2% of total step time to reconstruction and 52.5%
to flux/update work. Cross-file compiler optimization was tested separately
using `CMAKE_INTERPROCEDURAL_OPTIMIZATION=ON` in an isolated MSVC Release build.

The implemented source change materializes cell primitives once per immutable
RK stage, instead of repeatedly rebuilding them for slopes and opposite
faces. The cache is local to that stage and cannot persist stale values across
RK stages, wet/dry changes, or state replacement. Positive films are retained.
There is no resolution, timestep, boundary, friction, limiter, or equation change.
Extra storage is four doubles per grid cell (about 1.40 MB on this grid), with
the original slope and rolling-face storage unchanged.

| Isolated build | Total per requested step | Reconstruction per step | Flux/update per step |
| --- | ---: | ---: | ---: |
| Original, ordinary Release | 8.375 ms | 2.278 ms | 4.401 ms |
| Original, cross-file optimization | 7.580 ms | 2.196 ms | 4.218 ms |
| Primitive reuse, ordinary Release | 7.398 ms | 2.170 ms | 3.489 ms |
| Primitive reuse, cross-file optimization | 6.891 ms | 2.165 ms | 3.470 ms |

These are one isolated run per configuration, not confidence intervals or
repeated-until-pass results. All reports, executable and input hashes, command
lines, and stage counts are in `native-stage-profile/*.json`.

All four exported final 43,631-cell CSV fields, including derived normals and
Froude number, are byte-identical:
`7934382caa29e210eda346212eb82c8b838a620c6736bd74cd34aedcf5541109`.
The replay's reported mass drift is 7.064e-6 over ten seconds, with nonzero
external boundary discharge; this is not a closed-domain mass target.
All three CTest fixtures pass in both ordinary and cross-file builds:
wet/dry shoreline, lake-at-rest balance, and transcritical bump. The ordinary
build was then rebuilt with timers **off**, and all three passed again.

## Engine integration status

Only primitive reuse is being integrated into Unreal, **not** cross-file
optimization or profiling. The previous engine archive was checked against
its known hash before replacement and preserved at
`tmp/native-archive-before-primitives-20260907.lib`:
`d91b779b83c6b32d25518d4a284ed757d175758e2342a3b3649367b925a64155`.

Timer-free replacement `physics/cpp/build-ue/raftsim_water.lib`:
`fd988c73f10f2f1423b421fc3b6e78928d9124acba789e9fae05b75f1a51a35c`.
Engine rebuild session 72968 succeeded in 940.11 seconds (167 actions; existing
double-to-float damping warnings in the D6 Chaos runner). The registered map's
hash remains `81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.

Separate engine performance session 37515 exited 0. Same registered map,
review flags including activity memory, 1280×720 at 87%, RTX 3060 Laptop,
Development/offscreen, five-second warmup and twenty-second measurement;
no recording, profiling timers, or diagnostic readbacks. Report:
`survey_performance_native_primitives.json`.

- Mean frame **13.326 ms**, p95 **18.996 ms**; mean GPU **6.920 ms**.
- Average solver **8.085 ms**, versus previous **9.000 ms**.
- Zero wall-clock hitches over 33 ms; detail backlog at ten seconds 0.000976 s.
- Original 16.667 ms frame and 1.6 ms solver gates both still **fail**.

This is a modest improvement in the isolated engineering protocol, not
packaged/release qualification or a guarantee for every river. No repeated
runs until a favorable result. No visual improvement is inferred from timing.

## Engine regression result and stale guided default

Session 80903 exited 0, but its broader 25-test report is **not all green**:
`engine-native-primitives/index.json` has 22 clean successes, two successes
with warnings, and one failure. All fourteen detail tests and both spray
tests pass, as do the five replay fixtures and attainable-guidance unit test.
Captured-ground contact passes 20/20 cases (2,400 substeps); natural drift
reaches the original review map's outlet in 99.197 s, minimum sampled tube
clearance 40.134 cm, no missing ground queries, finite throughout. These two
map tests retain engine warnings. They use `SouthForkSurveyPlayable`, **not**
the registered-XY map or a full real-river navigation survey.

The guided test failed before driving: its default route still referenced
older enclosed-rock-gap fields. The default now names the existing
`guided-route-depth-limited.json`, matching the test's current map. Geometry,
field, depth-hash, 5 m route-error, 120 s outlet, and ground-clearance checks
are unchanged. Explicit overrides still undergo those checks.

Rebuild 23675 exited 0. Targeted corrected-default test 78792 also exited 0
but **failed its route-error assertion**: 9.938 m maximum error, versus 5 m.
It reached the outlet in 92.642 s, remained finite, had zero missing ground
queries, and minimum clearance 38.043 cm. This run used ordinary default
guidance, not the opt-in coordinated/attainable steering experiments; do not
attribute its difference from those earlier runs to primitive reuse.

Both failures are retained in the expanded **24-run** `guided-review.json`.
The setup correction is verified; robust guided traversal is not accepted.
All owned processes are terminal. Further CPU reduction, realistic foam and
spray, registered-map traversal, geographic acceptance, and the full remaining
queue are still required. No gate relaxation, scene promotion, or final commit.
