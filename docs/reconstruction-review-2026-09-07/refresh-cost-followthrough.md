# Normal-launch refresh cost localization — not acceptance

The latest uninstrumented900-frame failure is retained in guide-reentry.md:
mean34.250937ms/p9542.3028ms, versus earlier restored-normal
mean24.804112ms/p9533.7393ms. Both fail33.333333ms. Comparison of the existing
validated reports finds game-thread mean+9.43ms, surface Tick+4.75ms,
Refresh+3.34ms, solver StepWater+2.65ms, GPU+2.66ms. Nested scopes and
concurrent threads must NOT be summed or interpreted as independent causes.
These captures do not establish a causal effect of the rescue changes.

Using each report's explicitly confirmed nonlegacy offset1 grouping:

| Refresh / crest selection | Earlier count, mean frame ms | Latest count, mean frame ms |
| --- | --- | --- |
| Neither |261,16.90|54,19.64|
| Selection only |260,24.94|364,30.95|
| Refresh only |259,32.58|363,39.74|
| Both |1,40.18|0,unavailable|

Latest362of363 refresh-only frames exceed budget. A greater fraction of frames
do refresh work at the slower frame rate; this is not proof of more refreshes
per wall-clock second. A separate raw-scope count gives364positive refresh
samples in781rows versus261previously, and positive-refresh mean19.364ms
versus17.003ms. Raw scope rows and offset-aligned grouping are not identical.

Live process inspection confirmed original cook36692 and no other matching
engine/compiler/cook command. A3s CPU-delta sample showed the cook using20.05CPU
seconds; other listed consumers were each≤0.20s. That sample was outside the
profile, not proof of historical machine load or thermal state. Existing
capture receipts verify cook suspension. No system settings/processes changed.

## New instrumented localization

`south-fork-refresh-stages-v1-20260924` runs normal scenario start with the
existing `-RaftSimWaterStageTimings` probe,300CSV frames, unchanged solver,
geometry, refresh frequency and presentation. Engine exits0, no timeout,
original cook identity/suspension/resume succeed. Log SHA256:
`b7f4088e6d3a424b7322aea35e88562020fda1078b8b1f8185e2867708684e88`.
CSV SHA256:
`ef72af46c559e8db26caa44eb3657e4ccb810d791aae1ef3c4e9d36350b85138`.

All72refresh entries at engine frames60–240 inclusive are retained in this
summary. These are engine frame IDs, NOT CSV sample indices. Stage durations
are successive FWaterSurfacePerf marks; source_samples includes prelude/setup,
and foam_core_publish is a broad preparation region, not a claim of a second
mesh upload. Logging overhead prevents using this as acceptance timing.

| Stage | Mean ms | p95 ms |
| --- | ---: | ---: |
| Total refresh |18.51|20.17|
| Source sampling and setup |4.76|5.25|
| Foam/core preparation |3.78|4.38|
| Base vertices |2.59|3.01|
| Breaking carve |2.14|2.28|
| Hydraulic relief |1.50|1.62|
| Breaking detection |1.44|1.65|
| Optical filter |1.01|1.39|
| Shore/wake fields |0.82|1.16|
| Foam overlay finish |0.22|0.31|

Current code and the earlier cap-reference-and-review-inventory.md review
agree that an ordinary non-recenter refresh updates targets without issuing a
second core publication. Skipping interpolation on refresh frames would remove
the actual visible mesh update; no such edit was made. Base-vertex parallelism
also remains diagnostic-only after its prior unsuccessful whole-game controls.

Next split the source stage's recenter/allocation prelude from the already
fused sampling/handover cost before selecting an optimization; preserve exact
sample fields, masks, geometry and clocks. This run adds diagnostic evidence,
not a playable change, new source capture, motion/collision acceptance, or
completion of South Fork. Do not advance the river queue on these results.

## Source split and retained-scratch experiment — September24

The finer `south-fork-source-split-stages-v1-20260924` probe separates
88 refreshes at engine frames60–240: total mean19.13ms/p9521.17ms,
buffer/coverage setup1.79/2.16ms, fused sampling2.83/3.10ms and
clock/recentering0.05/0.07ms. This is instrumented localization, not a
performance comparison against the preceding probe.

`-RaftSimRetainRefreshScratch` now tests actor-owned allocations while resetting
every mask, float and sample on every refresh. Default remains local scratch;
no history, geometry reduction, solver or cadence change is enabled.
Editor build succeeds (240.93s). Native `RaftSim.Water.RefreshScratchReset`
passes with zero warnings/errors, including dirty/reset, growth, shrink and
empty arrays and restoration of upward sample normals. Receipt:
`tmp/refresh-scratch-native-v1-20260924/index.json`.

Actual normal-launch candidate source audit v2 reaches10.0069 world seconds:
50,625 samples, zero different samples, exact masks/probes/feather/heights,
all eight paired source passes exact. Report:
`tmp/refresh-scratch-source-audit-v2-20260924.json`, SHA256
`0472e90703db78f031150c146f711981963f12fad76597937f2b5cd427dfe8a7`.
The first300-frame audit exited before producing its report; it is NOT a pass.
The900-frame v2 deliberately crosses the10s trigger. This source audit excludes
later relief/foam/mesh results and is not whole-surface equivalence.

Separate, uninstrumented normal-start900-frame runs on this same Editor build,
four solver lanes, confirmed nonlegacy offset1, samples60–840 (781 rows):

| Allocation mode | Mean frame ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: |
| Default local control |32.894281|42.0352|46.0012|
| Opt-in retained candidate |28.364351|38.3631|46.3772|

CSV SHA256 control:
`32f2dc0685fdb9ccac04628fc7871d3a0475cc0153cf45410ddc2ea2736644b7`;
candidate: `a2e9b15adeb094f493689ab7cb1f24884e108ed8177ab84a1f6856bae3c57f51`.
Reports are `tmp/refresh-scratch-{control,candidate}-frame-v1-20260924.json`.
All four engine captures exit0 without timeout and their process receipts
confirm original cook36692 identity, suspension and successful resumption.

Both timings FAIL33.333333ms. One control-first pair does not establish causality
or sustained savings; slower maximum is retained. Candidate remains opt-in.
Next reverse/repeat the timing order, check downstream/recenter and final
surface/motion parity, then consider normal-play integration and Game rebuild
only if qualified. No new visible delivery, collision/shoreline acceptance or
river completion is claimed. Installed flow fields and nonlinear-off default
remain unchanged; no duplicate cook was launched.

## Reverse-order follow-through — promotion rejected

Revalidated the worktree and live original cook before running the same built
normal-start scene candidate-first, then local control. Both900-frame runs
exit0 without timeout; receipts confirm cook suspension/resumption and
nonlegacy offset1. Same60–840 inclusive781-row analysis:

| Allocation mode, in execution order | Mean frame ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: |
| Retained candidate v2 |34.459205|42.1934|49.2772|
| Default local control v2 |30.335400|40.1793|46.5106|

CSV candidate SHA256:
`2758f7f8eebeaee639c62a049e42914f2bbec945f05cc194f9fe5a8082a90ae8`;
control: `91d796ed1a65447d793253f22754c3edc96ab251f589ab3208a7d51c43f27958`.
Reports: `tmp/refresh-scratch-{candidate,control}-frame-v2-20260924.json`.
The candidate is slower in the reversed pair; all four captures fail the
unchanged33.333333ms gate. The earlier improvement therefore does not support
default promotion. Keep this candidate diagnostic-only and do not rerun this
unchanged whole-frame experiment expecting acceptance. Native/source equality
does not override its inconsistent measured cost. No new playable or visual
acceptance is claimed and no Game rebuild is represented as complete.

Next localize the broad foam/core preparation region (previously4.06ms mean),
including temporary packed attributes and target preparation, without skipping
interpolation, changing geometry, reducing refresh cadence or enabling the
broken nonlinear solver. Source split instrumentation remains available.
