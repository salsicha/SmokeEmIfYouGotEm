# South Fork metric breaking search - September 27

Candidate work; no new visual, hydraulic or performance acceptance.

## Actual current-state diagnosis

Unmodified packaged v8 (`98d30c3d56b7510599e1f3ec852b2a7e12c1808c507d0f918e2c139cd542bb3e`)
captured three paired GPU states at approximately10/15/20s. Session57232,
PID32476 completed exit0. Sources and hashes:
`tmp/sf-v8-breaking-transfer-20260927/live_{00,01,02}.json` and
`tmp/sf-v8-breaking-transfer-20260927/foam-audit.json`.
The existing density-to-coverage equation passes all three snapshots, maximum
error about1.04e-7, with no coverage on zero-weight cells. At10s the wet-cell
absolute perturbation median is0.000881m, p950.010495m and maximum0.063571m;
at20s median0.000747m, p950.009160m and maximum0.056739m. These are GPU detail
perturbations, NOT total wave heights or photographic measurements. The finite
depth detail simulation and accepted-source upload are active; replacing a
foam upload is not supported by these results. Sparse snapshots do not measure
a spectrum, turbulent energy transfer or full time history.

The actor log reports1m render spacing and analysis_stride=1. Consequently its
near/far upstream offsets cover1/2m, despite the detection comment specifying
two3m edges. An initial screen on the interpolated GPU source field motivated
capturing the ORIGINAL carrier inputs rather than claiming exact actor parity.

Input capture session88876/PID10776 completed exit0:
`tmp/sf-v8-front-input-20260927.csv` and `.log`.
CSV SHA256 `f86d080bcdb47ad75f143048e4841fb4fa2a38b5adb6df081830ff283f7da4ab`.
Screen recipe/result `tmp/analyze-sf-v8-carrier-fronts-20260927.py` /
`tmp/sf-v8-front-input-20260927-screen.json` identifies69 extended candidates
in a bounded interior subset; ten upstream positions are at least6m from
the39 logged original accepted raw sites. This screen uses rounded CSV values,
9.81 rather than engine9.80665 gravity and reconstructed conservative clearance;
it is NOT exact actor replay or proof that every row is a real breaking jump.
Some rounded six-metre offsets exceed6m Euclidean distance; the candidate below
rejects these, so screen counts must not be reported as native accepted counts.

Example current carrier path: downstream(-5462,3602), upstream(-5459,3603),
distance3.162m, Froude0.926 to1.188. Its one/two-cell upstream values are0.941
and0.968. The upstream point is8.944m from the nearest original raw accepted
site. Another six-cell path has a stronger1.379 upstream Froude but its6.083m
rounded distance exceeds the new strict6m limit. These are inferred hydraulic
transitions in the existing simulation, not measured boulder/wave coordinates.

## Candidate implementation

`RaftSimMetricBreakingSearch.h` preserves the original detections and supplies
an extension only when they find no supercritical upstream sample. It checks
3/6m metric offsets with a strict6m Euclidean bound. Every intermediate sampled
cell must remain live/wet; diagonal steps cannot cut dry corners. Direction
dot product must stay at least0.9 along the path (a conservative authored
alignment guard, not a measured river constant). Original0.94/1.12 Froude,
intensity, bank clearance, coverage and six-metre dedup gates remain intact.
Only normal Cartesian South Fork uses the extension; other rivers are unchanged.
`-RaftSimLegacyBreakingSearch` retains the old path for same-build comparison.
No water/foam amplitude multiplier, terrain/bed/source alteration, solver mode,
extra surface or acceptance-gate weakening is involved.

`RaftSim.P2.MetricBreakingSearch` covers physical scale across0.5/1/1.5m grids,
dry paths, opposed current, unchanged Froude thresholds, diagonal dry corners
and already-covered ranges. The original v9 test and five existing crest/support
regressions passed (six success, zero failures/warnings), native session78247,
`tmp/sf-v9-crest-regressions-20260927/index.json`.

V9 BuildCookRun session12165 completed exit0 in487.53s, using
`tmp/package-south-fork-v9-20260927.ps1`, log
`tmp/south-fork-v9-package-20260927.log`, fresh stage
`tmp/south-fork-playable-v9-20260927`. Same v7 runtime bundle and geometry.
Executable SHA256:
`ce37f9d898d9eddc73fe322c35033b35b52627fc46e7bf4ab9b30d20a84d401d`.
No repeat build/cook is needed for this exact candidate.

## Completed same-build motion comparison

Candidate capture32444 and legacy capture87953 completed exit0. Both use the
same normal FullReach scene, review8330m, AllForward paddling and ephemeral
profile. Only legacy adds `-RaftSimLegacyBreakingSearch`. Instrumented captures
are not performance qualification or identical-trajectory pixel comparisons.
Reports: `tmp/sf-v9-search-{candidate,legacy}-20260927.json`, corresponding
`.json.cartesian-mesh.json`, `-contact.json` and `.log`.

Candidate has14 persistent sites versus legacy10. Its submitted topology has
48,381 triangles versus46,605; both retain50,625 original source vertices.
Maximum submitted target error is0.795789cm versus0.795792cm; fine correction
tracking0.311002cm versus0.012445cm; original source displacement is zero.
More sites and triangles do not establish better breaking-water realism.

Candidate62 and legacy57 recorded contact projections all resample the current
ConveyanceGround mesh and match the solver float height. Largest recorded
vertical corrections are2.59963cm and1.76964cm respectively. These capped
observations are not a complete collision ledger or proof of a traversable line.

Videos in the v9 stage `Saved/VideoCaptures`:

- Candidate `RaftSim_20260927-134859.mp4`, SHA256
  `4a15b9e73fe50b9de9273c81ac65fcdca19013ab4ba0b59196708c8826daa45f`:
  773 decoded frames,25.7333s,12 exact adjacent duplicates.
- Legacy `RaftSim_20260927-135020.mp4`, SHA256
  `e923a71b95bf6aca1ce6675561bf9d90c4a062060be193bd282099a83878edff`:
  772 decoded frames,25.7s,two exact adjacent duplicates.

Decoded reports/frames: `tmp/sf-v9-{candidate,legacy}-decoded-20260927/`.
Original1s and20s frames from both were inspected; candidate6s was also reviewed.
Raft and paddles move toward the large rock and turn downstream. Both retain
broad flat foam, relatively smooth downstream water and coarse gray rock/bank
forms. No convincing visual improvement is established. Sparse frames do not
accept shoreline stability, full surface continuity or wave animation. Encoded
30FPS is not engine FPS. South Fork remains unfinished; do not advance Colorado.

## Follow-up source correction (not in staged v9)

Before the source correction, isolated packaged timing session79689 completed
exit0. Staged closure verified2,405 files/917,995,570 bytes against the unchanged
v7 manifest with no external fallback. Receipts:
`unreal/Saved/RaftSimValidation/sf-v9-{normal-menu,rapid11520}-20260927-frame-audit.json`.
Each audits1,140 of1,200 frames, with no runtime errors or diagnostic overrides.

| Launch | Mean ms | p95 ms | Max ms | Frames over100ms |20FPS gate|
|---|---:|---:|---:|---:|---|
| Normal Boot/menu |43.6728|56.3295|84.0096|0|FAIL|
| Busy11520m |83.3889|93.6782|134.7194|17|FAIL|

No build, cook or other owned game overlapped timing. This is not a controlled
same-build legacy timing comparison and does not prove the causal contribution
of the extension versus machine/run variability. It DOES fail qualification;
more detected sites cannot justify accepting this executable. Do not repeat the
unchanged v9 benchmark as a substitute for a corrected, measured candidate.

Review found an oblique-grid omission: at0.5m spacing,45-degree ray steps5/6
round onto the same cell, so the old early `continue` skipped the3m endpoint.
Steps11/12 similarly skipped the6m endpoint. Repeated cells now reuse path
validation but still evaluate the metric endpoint. Two endpoint regressions
include dry-path rejection. The map/feature selection is also hoisted outside
the per-cell search, without changing its conditions. Neither change alters
Froude, clearance, wetness, amplitude or physics gates.

Fresh editor build and native tests completed exit0 (session71385, testPID25240):
six success, zero failures or warnings, including the new repeated-endpoint and
dry-path cases. Recipe `tmp/validate-sf-metric-endpoints-20260927.ps1`, build log
`tmp/sf-metric-endpoints-20260927-build.log`, native report
`tmp/sf-metric-endpoints-20260927-tests/index.json`. No job remains live.

A subsequent game rebuild, actual motion and uncontended normal/busy performance
qualification remain required. The existing v9 executable and its results above
do NOT validate the corrected source. Preserve its failed qualification as
evidence, not an accepted release. No acceptance or visible delivery is claimed.

## Corrected v10 packaged validation

BuildCookRun87171 completed exit0 in386.59s, using
`tmp/package-south-fork-v10-20260927.ps1` and adjacent v10 package log.
Stage: `tmp/south-fork-playable-v10-20260927/Windows`. Executable SHA256:
`f67fb93b898d69b779fc6cda3d48f72d7191fb25ccce2f3d7e7ef98a45ae3303`.
This includes the repeated-endpoint correction and hoisted map guard; all
geometry, fields, optical settings and solver modes remain the v9 inputs.
Existing missing MetaHuman texture dependency warnings remain unresolved.

Staged closure passes2,405 files/917,995,570 bytes against the same v7 manifest,
with no source fallback (`tmp/south-fork-v10-staged-payload-20260927.json`).
Timing session41699 completed exit0: normal Boot/menu, busy11520m, then the
same busy station with the legacy-search reference. The profiler's optional
`-LegacyBreakingSearch` flag is explicitly recorded as
`diagnostic_legacy_breaking_search=true`, `normal_configuration=false`; it is
not normal playable qualification. Default runs retain the normal configuration.
All three runs use the same executable,1,200 frames/1,140 audited, with zero
runtime errors. Receipts under `unreal/Saved/RaftSimValidation/`:
`sf-v10-{normal-menu,rapid11520,legacy11520}-20260927-frame-audit.json`.

| Launch | Mean ms | p95 ms | Max ms | Frames over100ms |20FPS gate|
|---|---:|---:|---:|---:|---|
| Normal Boot/menu |40.0162|48.0122|62.6394|0|PASS this run|
| Busy11520m, default |51.5259|76.3335|106.3955|1|FAIL|
| Busy11520m, legacy reference |44.3918|50.9677|89.3852|0|FAIL|

No engine/build/cook overlap. Same-build comparison suggests added search/site
work contributes, but one sequential pair is not a controlled order-independent
causal estimate. Hash-bound summaries `tmp/sf-v10-recorded-cost-summary-20260927.json`
and `tmp/sf-v10-binned-cost-20260927.json` show default/legacy surface means
29.4794/24.8041ms, crest update11.4893/9.7568ms and selection6.8726/5.5456ms
(inclusive, do not sum). Default cost varies through the run, not only startup;
do not discard slow bins or increase warmup to turn the failure into a pass.

Motion2862/PID34956 completed exit0 after timing, recipe
`tmp/capture-sf-v10-metric-search-20260927.ps1`. Crest/mesh/contact reports share
`tmp/sf-v10-search-candidate-20260927` prefix. Fourteen sites,48,383 submitted
triangles; target error0.795794cm, fine tracking0.352530cm, source displacement0.
All61 capped contact projections match native ConveyanceGround/solver heights;
maximum1.51553cm. Not a complete traversal/collision ledger.

Stage video `RaftSim_20260927-141306.mp4`, SHA256
`bc4c4ea23d91a671efdc6a211a4ba0ebc2c48ab1ff5003da1555066a1542b0fd`, decoded
773 frames/25.7333s/six duplicates,1280x720. Report and original frames:
`tmp/sf-v10-candidate-decoded-20260927/`. Inspected1/6/20s: raft and paddles
advance, approach the rock, then turn downstream. Broad flat foam, smooth water
and coarse rocks remain; no convincing new breaking/recirculation realism is
established. Encoded30FPS is not game FPS. No full shoreline/surface-continuity
acceptance follows from these sampled frames. V10 remains NOT ACCEPTED.
No job from the v10 build/timing/capture sequence remains live.

Supporting v9 recorded-cost summary (no new engine run):
`tmp/sf-v9-recorded-cost-summary-20260927.json`, recipe
`tmp/summarize-sf-search-cost-20260927.py`. Hash-bound source CSVs retain1,140
audited frames and use the authoritative final header. Busy v9 mean game-thread
81.2347ms, GPU23.7099ms, surface tick56.2584ms, SetMesh21.1259ms, crest update
18.9971ms and selection12.1565ms. These scopes are inclusive: do NOT sum them
or mistake correlation for the extension's isolated causal cost.
