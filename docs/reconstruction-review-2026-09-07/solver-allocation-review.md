# Live solver cost review

September 7, 2026. Diagnostic performance work; no engine frame-time acceptance.

## Compiler experiment — not adopted

An isolated MSVC Release IPO/LTO build produced exactly the same saved CSV
fields as the corrected depth-limited baseline in three alternating 100-step
pairs. `depth-limited-lto-comparison/report.json` retains the initial wall-time
comparison. New CLI instrumentation separates solve/frame construction from
CSV export; old binaries report missing timings, never zero work.

The instrumented comparison in `depth-limited-lto-timed-comparison/report.json`
has median solve/frame-construction times 4.44436 s baseline versus 4.28748 s
LTO: only 3.53% less time. Wall-time reduction is 2.90%; export takes roughly
four seconds in each run. LTO is not adopted in the engine archive or default
build settings. These are offline measurements, not improved game FPS.

The instrumented baseline executable SHA is
`4aef216ca04d182b6acab6f920e982479e4ec523921bbd25771ec235a6a2565d`;
the instrumented LTO SHA is
`2237e78009b62aba75bcda1710fe6d84209c9c85ad4611136d0ed6cc0af36e4b`.
The initial LTO executable was rebuilt with instrumentation, so its old report
hash does not identify the current file. Raw logs/frames remain retained.

## Allocation candidate

The second-order RK stages read/write only h/u/v, but previously copied complete
WaterState arrays on every substep. The candidate retains per-instance primitive
scratch arrays and swaps fully recomputed final state allocations. Each stage
overwrites every primitive, including skipped exactly dry cells. No persistent
scratch is shared between solver instances. State replacement does not reuse
prior stage values; a fresh-versus-reused wet/dry replacement regression checks
all primitive and derived fields for exact equality. Boundary audits retain
their independent const scratch destination.

Build: `tmp/south-fork-muscl-scratch-20260907`. Three native CTest fixtures pass,
including the new scratch replacement regression. Benchmark results are recorded
separately in `muscl-scratch-comparison/report.json`: all saved fields are
byte-identical and all processes succeed. Median solve/frame time is 4.37727 s
baseline versus 3.63125 s candidate, **17.04% lower**. Median whole-process time
is 8.29672 versus 7.53519 s, 9.18% lower. Candidate executable SHA:
`f4190b0d0b7b68bd6bce2dc3fb6529872034506281d5b5c4542b44384016a357`.

The Unreal archive is rebuilt with SHA
`d91b779b83c6b32d25518d4a284ed757d175758e2342a3b3649367b925a64155`.
Its consumers were rebuilt together because the solver class layout changed.
The full editor build succeeded (930.27 s). Existing C4305 double-to-float
warnings in the D6 measured runner remain; this was not a warning-free build.

## Actual engine results

`engine-muscl-scratch/index.json` contains four passing tests: attainable
guidance math, depth-limited field replay, captured-ground contact and guided
traversal (two succeeded with warnings). Raw traversal
`unreal/Saved/Automation/SouthForkGuidedTraversal_20260907_175108.json` reaches
the outlet in 62.065 s, max route error 4.134 m, minimum tube clearance 31.685 cm,
586 wet samples, zero missing ground/grounded/unattainable samples. This is
another bounded route pass, not a continuous swept-collision or geographic proof.
The historical traversal ledger now retains 17 runs.

The clean offscreen 1280x720/87% protocol was run twice, without screenshots
or compiler work running concurrently:

| Run | Frames | Mean frame ms | p95 frame ms | Mean solver ms |
| --- | ---: | ---: | ---: | ---: |
| Prior depth-limited baseline | 1381 | 14.669 | 19.437 | 9.515 |
| Scratch first | 1343 | 15.063 | 20.283 | 9.380 |
| Scratch repeat | 1468 | 13.909 | 19.050 | 8.997 |

Reports: `survey_performance_muscl_scratch.json` and
`survey_performance_muscl_scratch_repeat.json`. Both fail the unchanged frame
and solver budgets. The offline 17% result does not translate into a demonstrated
17% game improvement; different timing conditions and cold/settled flow workload
need controlled profiling. Do not claim the performance issue is resolved.

Viewed actual captures `SouthForkGuidedTraversal_20260907_175108_001..003.png`
under `unreal/Saved/Screenshots`. They still show smooth water, directional
streaking and plain gray captured terrain; the finite review-domain edge is
visible in the later captures. These are not photorealistic or complete-river
acceptance. No map, material, flow-package or captured geometry was changed.

## Still required

The current local GPU detail is analytic procedural displacement, not a stateful
fluid simulation. This work does not turn it into one. The active engine still
advances the genuine finite-volume window; no timestep, grid, current, collision,
boat support or acceptance budget was reduced. Fine-grid engine integration,
actual crest/foam motion and geographic registration remain open.
