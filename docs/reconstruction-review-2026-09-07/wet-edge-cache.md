# Exact shoreline-distance reuse in ordinary play

September 18, 2026. A measured performance improvement, not completed water
realism or a 30 FPS pass. Full remaining project scope stays open.

## Change

Both Cartesian shoreline uses previously rebuilt the same eight-neighbor
distance transform. A surface-actor-owned cache now requires exact equality
of dimensions and every mask byte before reusing distances. No hash-only
match, stale shoreline, cadence reduction, distance cap, or altered physical
threshold is allowed. Changed inputs rebuild with the existing qualified
sweep. Returned arrays are owned copies; later calls cannot mutate earlier
consumers. World origin need not be keyed: this pure lattice-distance function
has no world-coordinate input.

`-RaftSimFreshWetEdges` retains uncached sweeps. The older
`-RaftSimReferenceWetEdges` and `-RaftSimWetEdgeSweepAudit=...` also bypass reuse,
preserving independent queue/sweep comparisons. `-RaftSimWetEdgeCacheAudit`
compares every distance on every enabled call with the original queue.
No material, terrain, water state, contact formula, solver timestep or rendering
quality changes. Nonlinear runtime remains OFF.

## Evidence before default promotion

Initial editor build passes in 217.84 s; incremental original-path preservation
build passes in 57.56 s. Existing DetailSourceFootprint C4701 and D6Chaos C4305
warnings remain. Five native tests pass with no test warnings/failures/not-run
in 0.629168 s: WetEdgeCache, WetEdgeSweep, CurrentOrientedBreakingRelief,
CartesianBoulderSurface and CartesianSurfaceGrid. Cache tests cover changing
dimensions with identical area, single-byte changes, dry/wet extremes, reset,
empty grids and caller immutability against the independent queue. Fourteen
report-parser positive/negative controls pass.

The complete 900-frame actual-game correctness capture checks **46,271,250
integer distances** in 914 calls, all exact. Both phases have 457 calls;
phase 1 has 76 hits and phase 2 has 457 hits. This includes changing live masks,
not just repeated synthetic arrays. Heavy comparison mode is excluded from
performance measurements. The report hashes its original log and process record.

Separate same-binary, four-lane, 1280x720 D3D12 FullReach station-8330 captures
use the predeclared A/B/B/A order. Every CSV row 60–840 is included, with verified
default elapsed-frame mode and scope offset one. Builds and heavy diagnostics
are terminal; the exact cook is suspended/resumed, with zero CPU increase during
each interval. Every game exits zero without timeout.

| Run | Cache | FPS | Mean frame ms | p95 frame ms |
| --- | --- | ---: | ---: | ---: |
| A | Off | 25.663296 | 38.966156 | 46.7528 |
| B | On | 26.250569 | 38.094412 | 46.1476 |
| C | On | 26.085509 | 38.335460 | 44.9717 |
| D | Off | 25.576125 | 39.098964 | 46.0913 |

Mean and p95 improve in both orders; mean reductions are 0.871744 and
0.763504 ms. Different trajectories and shared-machine variation remain limits
on attribution. All four still FAIL 30 FPS / p95 33.333333 ms. This supports
enabling exact reuse, not claiming the overall performance target is achieved.

## Final default verification

Default editor rebuild passes in 58.22 s; standalone Win64 Development game
build passes in 216.33 s. All five native tests pass again with NO experimental
enable flag: 0.643192 s, zero failed/warning/not-run tests. The related Python
bundle and audit group passes all 65 tests in 3.81 s. These are scoped checks,
not the whole-project release suite or packaged-game acceptance.

Fresh default gameplay timing, again all rows 60–840 of 900, is **24.985236 FPS,
40.023636 ms mean, 48.4048 ms p95: FAIL30**. It exits zero, no timeout, with
successful cook suspend/resume and zero measured cook CPU increase. This later
absolute result is worse than the earlier controls; retain it rather than
reporting only the best candidate. The earlier same-binary comparisons support
the local optimization, not a universal FPS gain or target acceptance. No fresh
calculation/cache enable flag is supplied in this final ordinary run.

Fresh ordinary lit motion at the same rapid start saves all 24 screenshots.
The entire 15.814 s video decodes successfully: 228 actual source frames,
474 encoded frames. Encoding may repeat frames; its 30 Hz timestamps are NOT
30 FPS gameplay. Unmodified 3 s, 9 s and 13 s frames were inspected: broad soft
foam, smooth mean wave faces, angular rock outlines and repeated tree crowns
remain visibly unresolved. The camera moves with the raft; that observation is
not robust traversal/collision acceptance. No new reference-video or physical
breaking validation is claimed. Fixed decoder ROI names are not semantic
measurements as the camera turns.

[Retained evidence](wet-edge-cache/) includes raw A/B/B/A and default CSVs,
process reports, exact-distance results, native and Python tests, full motion,
decoder reports and unmodified selected frames. Source assets/map and installed
hydraulic state were not changed by this optimization.

## Hydraulic continuation

Both 8950/local25000 and 9000/local26000 pass all 5,382,400 state cells and all
86,720 artificial-bank cells (exactly dry). Maximum step residual is
1.4754001131933592e-8 m3. The old cook PID8900/session68256 finishes normally,
exit zero, at its requested 9000-second endpoint. It was not restarted on a
timeout. An initial timing-launch attempt after completion refuses the absent
old process before starting a game; all actual timing runs use fresh v2 labels.

At 9000 s outflow is 102.7782629432 m3/s against inflow 45.3069545472 m3/s:
still NOT settled. The exact native continuation preserves all h/u/v values,
the clock, bed, grid, roughness, forcing, features and probes. No cells or water
are added; independent volume-sum discrepancy is 4.656612873077393e-10 m3.
Installed 4950 water stays unchanged.

New input: `tmp/control-ablation-9000to12000s-input-v1-20260918/manifest.json`,
SHA256 `02f3b5c73aff26adf5ccc93ae7a9ec3de17fc8545f5be7d17baa23e7ef1c99cb`.
Output: `tmp/control-ablation-9000to12000s-workers8-v1-20260918`.
Same solver SHA256 `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`,
60,000 steps at 0.05 s, snapshots every 1000 steps, eight workers.
Live identity at launch: PID13584, start UTC `2026-09-18T12:17:39.4321093Z`,
session95293. Revalidate liveness before control. Next 9050/local1000 requires
its completion marker and both independent audits.

Source provenance, the unresolved legacy float storage/face representation gate,
physical breaking/froth and full South Fork terrain/contact/traversal remain
open. No vertex snapping or tolerance relaxation was applied to that regression.
Colorado, then Pacuare and Futaleufu, Chilko/Zambezi reviews, crew, normalization,
all other regressions and final release checks remain queued. Troublemaker is
still a rapid inside South Fork, never a separate menu scenario.
