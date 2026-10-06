# Finer crest lookup: exact, but not a repeatable performance win

September 17, 2026. The 2 m index is NOT enabled or installed. No physical,
visual, motion, sustained-performance or scene acceptance is claimed.

## Candidate and correctness

`9d09dbdb9` added a compile-time tile-size variant of the existing immutable
8 m crest index. The non-shipping `-RaftSimFineCrestIndex` option substitutes
only the adaptive-refinement height function in the South Fork FullReach map.
The ordinary source-grid profile remains 8 m; candidate timing includes building
both indices. Site order, continuous evaluator, local/global caps, finite-support
padding, bounded-allocation fallback, geometry and refinement tolerances are
unchanged. No approximate interpolation, slower refresh or quality reduction.

The first test compile rejected an implicit integer-to-bool conversion; this
turn fixes it with an explicit comparison. The isolated build then succeeds.
Candidate DLL SHA256:
`ccfd252dfffe1d181969f10d17be1decfaaa97d33ac470004c53c97b89da9508`.
Installed gameplay DLL remains
`89b171f1a2031beb88b0e0a275a928b9acc1c9580b92616e7c4e64890302e410`.

Native report `tmp/fine-crest-index-native-v1-20260917/index.json`:
29 PASS, zero warnings/failures/unrun tests. The new test compares 398,145 exact
height/foam results against the full evaluator and coarse index: tile boundaries,
one-ULP neighbors, rotated/non-unit directions, local/global caps, distant cap
owners, legacy/invalid-direction fallback and index-capacity fallback.
Report SHA256:
`095299632709c78e0a80317714a39699106504fee87e09d694662f6d11d0f64e`.

Actual 1,200-frame `south-fork-fine-index-audit-v1-20260917` finishes exit0,
without timeout. Every query through the candidate refinement function compares
its result with the coarse index. All 627 logged profile epochs are retained:
626 positive-query epochs, one zero-query epoch, 125,947,647 queries and ZERO
mismatches. Startup confirms indexed=1, 1,140 occupied tiles, 1,551 dense slots.
This diagnostic is not ordinary FPS evidence. Completed log SHA256:
`7995e6387136692341ec97ef01fc3a281942d64f31d332e67331d3203807c18c`.

## Actual frame comparison: reject promotion

Same isolated binary, audit DISABLED, ordinary playable-map settings, 1280x720,
D3D12, 300 original samples per run. Inclusive rows60..240 give181 samples.
Execution order is coarse-a, fine-a, fine-b, coarse-b. All four exit0, no timeout;
the exact owned cook is suspended/resumed successfully around each capture.
Fine flags are confirmed active only in the fine runs; no audit epochs occur.

| Run | FPS | Mean frame ms | p95 frame ms | Mean crest update ms |
| --- | ---: | ---: | ---: | ---: |
| coarse-a | 28.168466 | 35.500691 | 41.6897 | 7.799149 |
| fine-a | 27.312398 | 36.613409 | 42.1879 | 7.796167 |
| fine-b | 27.768909 | 36.011497 | 42.0379 | 7.757436 |
| coarse-b | 27.599894 | 36.232023 | 41.1072 | 7.860775 |

The first pair worsens; the reverse-order pair has only a small mean-frame gain
and a worse p95. Both fine runs FAIL the unchanged 30 FPS / p95<=33.333333 ms
gate. Selection/crest cost differences do not establish a useful whole-frame
improvement. Do not promote this candidate or select only the favorable pair.
These runs are not independent same-input microbenchmarks or sustained release
qualification. Nested CPU scopes must not be added together.

CSV names: `south-fork-fine-index-{coarse-a,fine-a,fine-b,coarse-b}-v1-20260917`.
All original CSV hashes, metadata and scope metrics are retained in
`tmp/fine-index-abba-v1-20260917-audit.json`, SHA256:
`f41f9739c3c8ede57a94e95dca78263803cb65caebe84b164ad0d608691e34db`.
Nine frame-audit Python regressions and the PowerShell process-identity/profile
suite PASS. No new ordinary installed-binary performance or visual capture:
last installed25.907729FPS/p9544.7123ms still FAIL30. The unpromoted coarse
control is not relabeled as an installed-game result.

## Hydraulic continuation and remaining work

Same live PID17516/start2026-09-17T12:52:03.0749210Z, never restarted. Completed
4250s/local13000 passes state/conservation AND all86,720 exactly dry artificial
bank cells. Maximum depth3.896334730m, speed5.497125635m/s, maximum step residual
1.521822357e-8m3. Outflow97.843668598 versus inflow45.306954547m3/s:
NOT settled, NOT promoted. Reports:
`tmp/control-ablation-4250s-{state,banks}-v1-20260917.json`.
h SHA256 `06d0d6499ac6b9b000867445afe7031619d33e6b9d17e2578bc13d38c0ed9992`.
Next4300/local14000 requires a completed snapshot and BOTH audits.

This rejects tile-size reduction as the next performance fix; measured adaptive
sampling/evaluation remains expensive. Continue source-consistent terrain,
collision, hydraulics, breaking/froth and actual reference-motion validation;
do not substitute more tile-size sweeps for those missing results. Full ordered
South Fork -> Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi/all-scene water,
crew, normalization, regressions and release scope remains OPEN. Troublemaker
is a rapid within South Fork, never a scenario/menu entry.
