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
