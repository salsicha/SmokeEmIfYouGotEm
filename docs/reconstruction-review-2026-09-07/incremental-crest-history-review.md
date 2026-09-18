# Moving-coordinate crest history — September 18, 2026

Desktop target remains 30 FPS / p95 33.333333 ms. No mesh, quality, timestep,
crest/contact tolerance or physical acceptance gate changes. Troublemaker
remains a rapid within South Fork, never a selectable scenario.

## Workload evidence

The previous ordinary capture has 181 updates, 64 coordinate changes and 64
profile changes; zero coordinate-only changes. The new stage capture also has
zero coordinate-only changes. Reusing immutable profile heights between builds
would therefore not address this measured workload; it was not implemented.

Two complete 300-row instrumented captures use 1280x720 D3D12, fixed CSV rows
60–240. Their p95 values are 46.6753 ms and 37.5592 ms; both FAIL30.
Differing trajectories and instrumentation do
not establish any speedup. Report:
`tmp/crest-publication-instrumented-frame-v1-20260918.json`.

New opt-in `WaterCrestVertices` timings subdivide the existing vertex stage
without changing work. The subdivided capture retains every engine frame
60–240, 181 calls. Means: copying 0.699841 ms, midpoint expansion 0.257303 ms,
history 0.796582 ms. History costs 0.313474 ms in 118 stable-coordinate calls
versus 1.701452 ms in 63 remapped calls. This identifies remapping as a useful
target, not a measured candidate improvement. Existing outer stages include
additional validation work; do not add nested timings together.

Reports: `tmp/crest-publication-stages-{baseline,subdivided}-v1-20260918.json`.
Log SHA256 baseline:
`51b3dcca5dd347794ef2307e79a89a42043d3979b07ccef1e68c8e0b28229306`.
Subdivided:
`67515230ed4edeed063c49539ed0caf16ad2728c0c7fc678a55ad1e1e0553442`.
Both captures exit0, no timeout; the same owned cook is resumed in finally.

The original process record rounded the cook start through CIM to microsecond
precision. The strict profiler correctly rejected that value before suspension.
Direct retained-process inspection gives the full precision start UTC
`2026-09-18T04:30:27.5746992Z` for PID28776, executable and command line unchanged.
Use this verified timestamp for future process control; do not weaken matching.

## Candidate tested and rejected for production

`FRaftSimIncrementalCrestHistory` retains exact-coordinate membership in sorted
index lists. Old corrections are consumed before any ownership is changed.
Unchanged nodes retain their previous last-index owner; moved nodes query the
original previous map. Sparse membership updates remove old entries and insert
new entries in index order, then update every affected duplicate's owner.
Large regroupings or changed counts rebuild membership. Every height, target,
boundary and temporal blend still updates; no profile or correction is frozen.

The initial `-RaftSimIncrementalCrestHistory` gameplay switch has been REMOVED
after the failed comparison below. Only the explicit diagnostic
`-RaftSimIncrementalCrestHistoryAudit` remains; it always publishes the reference
history, never the candidate. Its paired audit keeps both
histories warm from startup, compares every current attribute and correction,
and measures all 64 alternating-order pairs on frames120–183. A second capture
must repeat the result before promotion. Verification is recorded below;
no ordinary-game acceptance is claimed.

73 focused Python checks PASS, including malformed/missing timing evidence,
existing topology-publisher audit, runtime budgets and shared-water contract
mutations. `tmp/crest-incremental-focused-v1-20260918.xml`.

Initial editor build succeeds478.56s; the additional sparse-group stress fixture
build succeeds20.06s. Eight native D3D12 tests PASS, no warnings/failures/not-run,
1.042517s. The original36-frame history fixture compares all attributes against
its independent serial map; a separate160-frame fixture tests whole duplicate
groups moving to new coordinates, merging and resetting. Fine-crest/contact,
target-cache, midpoint and topology tests pass, as do CareerCatalog and
ProgressionMigration. Report `tmp/crest-incremental-native-v1-20260918/index.json`,
SHA256`6f06c05e63fbb85f1dd617401b6db17b30a4584195caf3e0f1f4da196fc696d9`.
These results precede the subsequent work-selection adjustment below.

First actual trial `south-fork-incremental-history-pair-a-v1-20260918` exits0;
all64 logged pairs are exact, but NONE exercises incremental membership.
33 calls rebuild fully and31 are dense: about2,200 changed nodes exceed the
initial1/8-of-midpoints cutoff. Reference-first mean0.551756ms versus candidate
0.618587ms loses; candidate-first1.829950 versus1.600691ms improves. The strict
auditor rejects missing sparse-path coverage. This is NOT qualification.

The revised opt-in trial uses a1/4 work-selection cutoff and avoids repeating
per-node XY equality when whole-frame equality was already established. This
changes no coordinate, arithmetic, ownership or tolerance. It needs a fresh
native run and TWO new actual-input comparisons; neither prior timing nor
the unexercised sparse path counts toward qualification.

Revised build392.69s succeeds. All eight native D3D12 checks PASS again,
zero warnings/failures/not-run,0.917949s. Report:
`tmp/crest-incremental-native-v2-20260918/index.json`, SHA256
`d33e6bab16722a06f69a8026fb542ae2774a93cbff5ea1a2c826a9a9becfd7d3`.

Revised actual capture `south-fork-incremental-history-pair-b-v1-20260918`
exits0 with all64 pairs exact.32 calls use sparse updates,32 are dense.
Reference-first/sparse mean1.942994ms versus candidate1.855200ms improves,
but candidate-first/dense0.326659ms versus0.420378ms loses. Overall means
1.134827 versus1.137789ms: slightly WORSE. Workload and call order correlate
in this trajectory; do not generalize a mode advantage as an order-only effect.
The strict auditor returns failure. A second qualifying capture cannot repair
this failed first capture, so no repeat is used to select a favorable result.
Report:`tmp/crest-incremental-pair-b-review-v1-20260918.json`.
Log SHA256`3b35c61200eab88fd5026d01bd43a593e7bb7550395a670459fe381a6c515b4c`.

Decision: reject production use and remove the gameplay switch. Retain the
explicit same-input diagnostic and regression fixtures to make the rejection
reproducible. No performance, visual, physics or scene improvement is claimed.
Final diagnostic-only editor build succeeds21.54s. Final74 focused Python
tests PASS, including a source guard that the candidate cannot publish gameplay
vertices. XML:`tmp/crest-history-final-python-v1-20260918.xml`, SHA256
`114fb144b7168e8a2539f8cf453f6ca45bc3a778144d73971ff0522f279ab436`.
All eight final native D3D12 tests PASS, zero warnings/failures/not-run,
1.096259s. Report:`tmp/crest-history-final-native-v1-20260918/index.json`, SHA256
`523a1006f9de359a37c38a04b8d58a9ba5c6b3b07fa29576bdb5406b7c49477e`.

Final ordinary capture has NO timing/audit/candidate flags.1280x720D3D12,
300 CSV rows, fixed60–240:32.310929FPS average, p9541.7264ms, still FAIL30.
Report:`tmp/crest-history-normal-final-review-v1-20260918.json`;
CSV SHA256`e044e5731e88afca3302beab849a90060730e366d7433b8e2e7daace4b020e08`.
The game exits0 without timeout; identity-checked cook suspension/resume both
succeed. This is not a controlled speedup, sustained or packaged qualification.
No new visual capture/reference review or visual improvement is claimed.

## Hydraulic state and remaining scope

7300/local2000 and7350/local3000 pass BOTH full-state and artificial-bank audits.
All5,382,400 cells are finite;86,720 artificial-bank cells stay exactly dry.
7350 volume2,663,037.454902m3, maximum depth3.813094378m,
speed5.344215363m/s, maximum step residual1.419416e-8m3. Outflow107.837439m3/s
still exceeds45.306955m3/s inflow: NOT settled; installed4950 stays unchanged.
Reports: `tmp/control-ablation-{7300,7350}s-{state,banks}-v1-20260918.json`.
7350 depth SHA256:
`9e02b301b49fc55e71af54675a31557274371c0ce962f27c6e5d1970db4762ec`.
7400/local4000 also passes BOTH audits: volume2,659,864.892993m3,
maximum depth3.813902109m, speed5.345173053m/s, same maximum step residual.
All86,720 artificial-bank cells remain exactly dry. Outflow108.484623m3/s
still exceeds inflow45.306955m3/s: NOT settled, not integrated.
Reports:`tmp/control-ablation-7400s-{state,banks}-v1-20260918.json`;
depth SHA256`50f89d5208d7a87cb31fce7cabcc89015926e8874a0af9c6b03c2631850c5b92`.
7450/local5000 passes BOTH audits too: volume2,656,724.164756m3,
maximum depth3.814467020m, speed5.346014013m/s, same maximum step residual,
and86,720 exactly dry artificial-bank cells. Outflow109.092012m3/s still
exceeds45.306955m3/s inflow. Reports:
`tmp/control-ablation-7450s-{state,banks}-v1-20260918.json`;
depth SHA256`e4d71278b8571989cf16dac68112b70975aa4fe45add9100634686b6b3650b25`.
The same cook remains live. Next7500/local6000 requires its complete marker
and both audits. Nonlinear runtime remains OFF; no unsettled state is promoted.

No new visual or physical acceptance. South Fork reconstruction, flowing and
breaking single-surface water/froth,30FPS, then Colorado/Pacuare/Futaleufu,
Chilko/Zambezi, crew, normalization,13 physical regressions and release remain
required. This optimization work does not substitute for those requirements.
