# Corner-first crest range experiment

September 18, 2026. No visual improvement or30FPS acceptance is claimed.

## Question and implementation

Adaptive selection first tests a conservative profile-height interval before
sampling triangle corners and quarter points. A sampled corner spread greater
than the0.5cm tolerance proves that the interval cannot reject that triangle.
The experiment samples those corners first and bypasses only that unhelpful
interval query. It still uses every original quarter-point error test; a steep
linear plane must not refine merely because its corner spread is large.

The candidate preserves the current continuous profile, three refinement levels,
detail window, original source positions, triangle order/ownership and unchanged
2cm independent interior gate. No prior-frame height or selection is reused.
The immutable-profile requirement remains mandatory.

## First actual-game result: slower

The initial editor build succeeds in243.46s. Native checks initially ran with
NullRHI:8PASS/1FAIL. `RaftSim.M4.ShorelineFineCrest` correctly requires a non-null
actual rendering proxy, so that invocation cannot qualify it. The failure is
retained in `tmp/crest-corner-range-native-v1-20260918/index.json`; its geometry
subchecks did not replace the failing proxy assertion.

A separate D3D12 run completes9PASS with zero warnings/failures/not-run tests:
`tmp/crest-corner-range-native-d3d12-v1-20260918/index.json`. It includes the new
corner-range test, the original range/interval and fine-crest tests, conforming
refinement and four committed-clock tests. No native assertion was weakened.

The first FullReach gameplay capture contains64 alternating same-input pairs
after two warmups, frames125..245. Every pair preserves ordered parents,
triangles, original owners, expanded coordinates and production topology.
Timing includes the whole adaptive build, not just the skipped bound calls.

| Call order | Reference mean ms | Candidate mean ms | Faster candidate pairs |
|---|---:|---:|---:|
|Reference first|5.139965564|5.474721896|6/32|
|Candidate first|4.868949996|5.161478068|5/32|
|All|5.004457780|5.318099982|11/64|

The candidate is slower in BOTH orders. Eager corner sampling is not justified
by fewer interval calls. The gameplay switch is removed; the candidate remains
an explicit compile-time comparison specialization only, never the default.
Ordinary callers compile the original range-first ordering without a new
per-triangle candidate switch. Final-build verification is recorded below.

Raw pairs: `tmp/crest-corner-range-pairs-a-v1-20260918.json`, SHA256
`17cef411d1a1c3982ddf5a61e9e8adbac1c735d5ec89f0434ca2f633d1aee758`.
Summary: `tmp/crest-corner-range-pairs-a-summary-v1-20260918.json`.
Process/log/CSV prefix: `south-fork-corner-range-pairs-a-v1-20260918`.
The600-frame game and its wrapper exit0 without timeout. Solver archive and
four-lane override are confirmed; the exact cook identity is suspended/resumed
successfully. Instrumented frame timings are NOT used for30FPS acceptance.
The strict report adapter and its unchanged shared validator pass22 Python tests.

## Final compiled implementation and ordinary gameplay

The final editor build succeeds in219.04s, followed by9PASS/zero warnings or
failures in the same native D3D12 checks. Final native report:
`tmp/crest-corner-range-final-native-v1-20260918/index.json`, SHA256
`0501448b3083ce0910a157168e073d8d472afa742a5582189bd2b9610642f718`.
Build log: `tmp/crest-corner-range-final-editor-build-v1-20260918.log`, SHA256
`0c01a3c9cf7eb7101ca1905d2c7837f0e6165f4bad6a72df3e4c2c617fa71c2d`.

A second actual-game capture checks the final compile-time specialization,
again64 alternating pairs, frames125..251, all geometry/production comparisons
exact. It also loses BOTH orders:

| Call order | Reference mean ms | Candidate mean ms | Faster candidate pairs |
|---|---:|---:|---:|
|Reference first|5.012818961|5.310871871|6/32|
|Candidate first|4.972050549|5.246065557|3/32|
|All|4.992434755|5.278468714|9/64|

Raw report: `tmp/crest-corner-range-pairs-b-v1-20260918.json`, SHA256
`f7b58b131cb29cad93de353009d808d1c1da310d925d91f9660c54ed2d37690a`.
Summary: `tmp/crest-corner-range-pairs-b-summary-v1-20260918.json`.
The two captures are different gameplay trajectories/builds, not identical
states across runs; each individual pair uses the same current inputs.

The separate900-row ordinary run has no comparison instrumentation. Fixed
inclusive samples60..840 give mean38.95948540332906ms,25.6676901567738FPS,
p9547.2797ms: FAIL30 and the33.333333ms p95 budget. This is not evidence of a
speedup or a newly caused slowdown against earlier variable gameplay runs.
Normal FullReach, station8330,1280x720D3D12, four solver lanes and unchanged
physics/quality/geometry are retained. The confirmed default FrameTime mode
associates elapsed samples with the preceding logical frame; no phase fitting
or trimming of requested rows is used.

CSV: `unreal/Saved/Profiling/CSV/south-fork-corner-range-final-normal-v1-20260918.csv`,
SHA256 `8cb5ba845642b1c44d5726700a0a2a9c502f3d9c6a5581b1d1e659e85940aad8`.
Frame audit: `tmp/crest-corner-range-final-normal-frame-audit-v1-20260918.json`,
SHA256 `d56c71796cdb3c2d0b47e4bd4731689343b0f5f01760b18dcdfd40bba7b5891d`.
All three game/wrapper exits are0, no timeout, matching lane/archive/mode logs,
and successful exact-identity cook suspension/resumption. CSV and log hashes
were rechecked after all captures. No reference-video or new motion/visual
acceptance is claimed by these timing captures.

## Hydraulic state and remaining work

8150/local9000 independently passes BOTH state and artificial-bank audits:
5,382,400 cells,86,720 artificial-bank face cells exactly dry, maximum depth
3.8013897411978874m, maximum speed5.351516477733153m/s, maximum step residual
1.4395798775268531e-8m3. Outflow100.52750870491465m3/s still exceeds inflow
45.30695454719997m3/s; NOT settled and installed4950 water is unchanged.
Reports: `tmp/control-ablation-8150s-{state,banks}-v1-20260918.json`;
depth SHA256 `4cccc12a50ceb784ea2d03fce221c7d56519fa669d7c97a3ccd4718e1b9345ff`.

8200/local10000 also passes BOTH audits with the same cell/bank counts and
maximum residual. Maximum depth3.799528993323513m, speed5.351679034139247m/s,
outflow103.82835109630411m3/s versus unchanged45.30695454719997m3/s inflow:
still NOT settled. Reports `tmp/control-ablation-8200s-{state,banks}-v1-20260918.json`;
depth SHA256 `24614a4adf8fed37fc160147c45fed4f8aae5c267cec139733df642d98b53f6c`.

The same cook8900/startUTC2026-09-18T06:34:59.2598919Z/session68256 continues.
It was revalidated live after the final capture; next8250/local11000 needs its
complete marker and BOTH audits. Do not repeat eager-corner range ordering as
a speedup candidate without new evidence: both actual-game histories reject it.
No solver, physical input, contact gate or rendering quality is reduced.
Nonlinear runtime remains OFF. Breaking/froth visuals, coupled nonlinear
physical-momentum/interface work and the30FPS/p95 gate remain open, followed by
the full ordered scenario, crew, normalization, regression and release scope.
