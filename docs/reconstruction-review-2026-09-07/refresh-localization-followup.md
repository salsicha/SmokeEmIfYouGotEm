# Packaged refresh localization follow-up

2026-09-24. Supporting diagnosis only; no playable changes or acceptance.

Ran the current normal staged executable through default Boot and the normal
menu StartScenario handler into south_fork_full_descent, with existing detailed
water timers and 900 post-travel CSV frames. D3D12, adapter 0, 1280x720,
RenderOffscreen; no cook or engine build was live. Terminal process exit 0,
normal shutdown and solver-worker join. No new executable or cooked assets.
This is not physical menu/input dispatch or visual inspection.

The diagnostic emits verbose per-frame logging; its wall-clock costs must not
be compared directly to the earlier uninstrumented 34.352297ms/41.6848ms
mean/p95 acceptance run. It is not a new performance qualification.

721 refresh calls at engine frames 120..840, successive timer intervals:

| Interval | Mean ms |
| --- | ---: |
| Total refresh | 33.8097 |
| Source samples | 5.4753 |
| Base vertices | 3.8360 |
| Buffer/coverage setup | 3.7582 |
| Breaking carve | 2.8433 |
| Breaking detection | 2.7365 |
| Hydraulic relief | 2.3104 |

All remaining intervals are retained in
tmp/south-fork-refresh-localization-20260924.json (SHA256
83394387a0967413ebbf525e6b8973c89d8405cb00e1bb72dbfeaa11de98e59e).
Raw log: tmp/south-fork-refresh-localization-20260924.log.
Reproduction/parser: tmp/summarize-refresh-localization-20260924.py.
CSV scopes are nested; do not add them to these successive intervals.

Read the existing refresh-cost-followthrough rejection record before acting:
retained scratch and parallel presence already failed repeat-order gains.
Do not repeat those unchanged candidates.

New code-inspection candidate: the breaking detection loop computes hydraulic
direction and an upstream grid index before rejecting a non-live-wet current
cell, then rejects local Froude > 0.94. Those current-cell predicates require
neither direction nor upstream access. FlowDirectionFor is a pure coordinate
calculation. Test moving these unchanged rejection predicates ahead of that
work, preserving NaN comparison semantics, live/baseline ownership, scan order,
all remaining thresholds, accepted site sequence and persistent-site updates.
No edit or speed claim yet. Require native output parity, actual normal-play
comparison and geometry/motion review before treating it as delivered work.

South Fork remains first and unfinished. No later river was started.

## Early-gate candidate and build interruption

Added opt-in RaftSimEarlyBreakingGate in the existing detection scan. It moves
only current-cell dry/Froude rejection before pure direction/upstream lookup;
the original downstream predicates, ordering and thresholds remain. A native
BreakingCandidateGate test covers both coordinate modes, three strides, masks,
boundary indices, several directions, threshold neighbors, infinities and NaN.
The test is written but NOT executed or accepted yet.

Editor build session34110 stalled before emitting a build log or compiler work.
Read-only process inspection identified dotnet parent5576 and child32292,
both created2026-09-24 08:42:47 local. An identity-checked cancellation stopped
the parent (session terminal exit1); Windows initially denied termination of
child32292. A subsequent process check found BOTH processes absent, so the
attempt is terminal and an escalated build retry was started. No failure has
been called a pass.
The candidate remains disabled by default and unstaged.

Escalated editor retry completed successfully in91.06s. Native automation
RaftSim.Water.BreakingCandidateGate passes1/1 with zero warnings/errors:
86,688 comparisons,48,048 early rejections. Report:
tmp/breaking-candidate-gate-native-20260924/index.json. This proves the scoped
predicate fixture, not actual scene output or a speed improvement.

ABBA orchestration: tmp/run-breaking-gate-abba-20260924.py. First control-a
run produced repeated ZenLocal PutCacheRecords HTTP507 Insufficient Storage
errors during startup; disk check showed1,161,007,104bytes free. No usable
comparison or acceptance is claimed. Identity-checked cancellation stopped
only runner13920 and childUnrealEditor21220 (session53420 terminal exit1),
preventing subsequent candidate/control runs. Logs preserved at
tmp/breaking-gate-control-a-20260924.log. Do not repeat until storage recovers.
Actual-input parity, clean same-build timing and playable integration remain
required; installed staged game and geometry/physics defaults are unchanged.

## Recovered storage and clean ABBA timing

Lossless NTFS compression of183terminal diagnostic arrays recovered available
space to5.97GB; all pre/post hashes match, no deletions. See
diagnostic-storage-recovery.md. Retry checks3GiB before each run and refuses
further comparisons on a storage error. It completed all four runs, exit0,
no Insufficient Storage or fatal-error matches. Every log confirms
csv.UseLegacyFrameTime=false. Normal Boot/menu-handler/FullReach, same Editor
build,900frames each,1280x720D3D12, ephemeral profile, unchanged four solver
lanes/quality/physics; no concurrent build, cook or compression.

Unchanged audit window rows60..840 (781samples), offset1,30FPS target:

| Run | Mean frame ms | p95 ms | Mean refresh ms |
| --- | ---: | ---: | ---: |
| Control a |35.407344|43.3611|9.545489|
| Candidate a |34.350773|43.1782|8.871510|
| Candidate b |34.060595|42.1438|8.944317|
| Control b |35.127144|43.1627|9.499050|

Both orders favor the candidate's mean, p95 and refresh cost. All four p95
values still FAIL33.333333ms. These are bounded Editor game runs, not packaged
delivery, sustained/full-route acceptance or proof of geographic realism.
Raw process receipt: tmp/breaking-gate-retry-abba-20260924.json.
Per-run reports (including CSV SHA256) and logs use the prefix
tmp/breaking-gate-retry-{control-a,candidate-a,candidate-b,control-b}.
Actual-scene survivor/output parity and packaged/default integration remain
next; do not keep repeating this completed ABBA comparison unchanged.
Candidate is still opt-in; no installed executable or fields were replaced.

## Actual-input parity and normal staged delivery

The preceding opt-in status is superseded by this section. Editor audit build
passed42.73s. A normal-menu actual-input audit checked64refreshes,3,240,000
current-cell decisions,2,568,384early rejections and zero differing survivors.
Log: tmp/breaking-gate-actual-parity-20260924.log, SHA256
1ad9de669d546e2e682efe5fce249c20ebf7d0af354bec0cd2dda2dda083af28.
Normal shutdown was observed and the process was confirmed absent. This is
predicate/survivor parity; the downstream scan code and ordering are unchanged.
It is not a new full-route physical or geographic acceptance test.

Enabled early rejection by default only for Cartesian South Fork FullReach.
Other rivers retain the original behavior. RaftSimReferenceBreakingGate keeps
the original path available; diagnostic audit remains opt-in. Game build
passed138.39s. Staged executable replaced after verified backup:

- New SHA256:6194fed46b8dbf4a37c9948112cdc54052ed96dbc792ded7bfc1f8cc3bc04ddd.
- Backup SmokeEmIfYouGotEm-pre-breaking-gate.exe SHA256:
  394d06c94b22918ba83afac9a3831991d76229dac5ba955acdfcfea7b486726e.
- Stage:tmp/standalone-stage-deferred-normal-v7-20260924/Windows/SmokeEmIfYouGotEm/Binaries/Win64.

No cooked content, geometry, source data or hydraulic fields replaced.

First staged normal-menu900frame check exited0, wet raft motion logged, but
mean80.769837ms/p9588.0312ms FAIL. This failure is retained in
tmp/breaking-gate-staged-normal-frame-20260924.json. It was launched under
restricted execution unlike the prior elevated Editor ABBA. Both CPU and GPU
times were much higher; the root cause is NOT established by this observation.

Same staged executable, fresh sequential normal-menu checks under the elevated
execution used for Editor timing, same resolution/settings/window/offset:

| Path | Mean frame ms | p95 ms |
| --- | ---: | ---: |
| New default |36.560982|43.5522|
| Original reference override |37.233458|44.3437|

Both exit0 and confirm nonlegacy timing, both FAIL33.333333ms. Reports:
tmp/breaking-gate-staged-{default-elevated,reference-elevated}-frame-20260924.json.
This single staged pair corroborates direction only; do not attribute the much
larger cross-permission timing difference to this optimization. No30FPS claim.

Separate direct-map visual run (NOT frontend navigation) exited0 and captured
12images at0.5s intervals after10s. Actual staged screenshots002and011 were
inspected: crew/raft/terrain render, water patterns and viewpoint change;
surface remains smooth and shows pixelated/speckled water patterns. Their
appearance alone does not identify foam rather than optical contributions. Not convincing
crest/froth realism, full shoreline stability or full collision validation.
Images: staged Saved/Screenshots/breaking-gate-staged-20260924_000..011.png.
Log:tmp/breaking-gate-staged-render-20260924.log. No further work was live when
the checks completed. South Fork and the complete ordered queue remain open.

## Staged rapid motion follow-through — September 24

Bounded direct-map review now exercises this same staged executable at8330m,
not just the normal starting reach. Executable SHA256 remains
`6194fed46b8dbf4a37c9948112cdc54052ed96dbc792ded7bfc1f8cc3bc04ddd`.
No replacement geometry, source field, material, solver mode or optimization
override was supplied. This explicit review start is NOT normal-menu traversal;
the normal-menu performance evidence above remains the applicable measurement.

Reproduction: `tmp/review-staged-troublemaker-20260924.py`; engine exit0,
eight requested stills, complete recording decode322frames through10.7s,
one exact adjacent duplicate. Recorded rate is not game FPS. Movie SHA256:
`80bd404ba4aea9128a3f7258b00fc96639aa09c5894774b52f0f123679858b78`.
Decode report: `tmp/staged-troublemaker-decoded-20260924/report.json`.
Log: `tmp/staged-troublemaker-motion-20260924.log`.

Inspected original stills000/007 and decoded3s/9s frames: broad blurred white
coverage and smooth faces remain, with a large angular rock close ahead of the
raft. The raft turns and moves past this view; no whole-water disappearance is
visible in these inspected frames. These are not full shoreline/contact checks.
The first four stills localize a brief near-stall: station8343.554→8343.151m
while raft yaw14.517→54.901degrees; final still8349.758m/yaw124.599degrees.
Wet support telemetry persists, but this does not distinguish physically valid
rock deflection from inaccurate collision or flow. Do not flatten the rock,
alter collision or change steering solely to remove this observed interaction.
Next geometry/contact work should compare this localized interaction with the
existing shared render/collision source and evidence uncertainty.

This is additional staged validation of the already-delivered increment, NOT
new rendered reconstruction or acceptance. No new cook/build was started;
South Fork remains first unfinished. Avoid repeating this unchanged capture
or the already-rejected foam-only/normal/reflection trials as progress.

## Actual-input parity and normal staged delivery

The preceding opt-in status is superseded by this section. Editor audit build
passed42.73s. A normal-menu actual-input audit checked64refreshes,3,240,000
current-cell decisions,2,568,384early rejections and zero differing survivors.
Log: tmp/breaking-gate-actual-parity-20260924.log, SHA256
1ad9de669d546e2e682efe5fce249c20ebf7d0af354bec0cd2dda2dda083af28.
Normal shutdown was observed and the process was confirmed absent. This is
predicate/survivor parity; the downstream scan code and ordering are unchanged.
It is not a new full-route physical or geographic acceptance test.

Enabled early rejection by default only for Cartesian South Fork FullReach.
Other rivers retain the original behavior. RaftSimReferenceBreakingGate keeps
the original path available; diagnostic audit remains opt-in. Game build
passed138.39s. Staged executable replaced after verified backup:

- New SHA256:6194fed46b8dbf4a37c9948112cdc54052ed96dbc792ded7bfc1f8cc3bc04ddd.
- Backup SmokeEmIfYouGotEm-pre-breaking-gate.exe SHA256:
  394d06c94b22918ba83afac9a3831991d76229dac5ba955acdfcfea7b486726e.
- Stage:tmp/standalone-stage-deferred-normal-v7-20260924/Windows/SmokeEmIfYouGotEm/Binaries/Win64.

No cooked content, geometry, source data or hydraulic fields replaced.

First staged normal-menu900frame check exited0, wet raft motion logged, but
mean80.769837ms/p9588.0312ms FAIL. This failure is retained in
tmp/breaking-gate-staged-normal-frame-20260924.json. It was launched under
restricted execution unlike the prior elevated Editor ABBA. Both CPU and GPU
times were much higher; the root cause is NOT established by this observation.

Same staged executable, fresh sequential normal-menu checks under the elevated
execution used for Editor timing, same resolution/settings/window/offset:

| Path | Mean frame ms | p95 ms |
| --- | ---: | ---: |
| New default |36.560982|43.5522|
| Original reference override |37.233458|44.3437|

Both exit0 and confirm nonlegacy timing, both FAIL33.333333ms. Reports:
tmp/breaking-gate-staged-{default-elevated,reference-elevated}-frame-20260924.json.
This single staged pair corroborates direction only; do not attribute the much
larger cross-permission timing difference to this optimization. No30FPS claim.

Separate direct-map visual run (NOT frontend navigation) exited0 and captured
12images at0.5s intervals after10s. Actual staged screenshots002and011 were
inspected: crew/raft/terrain render, water patterns and viewpoint change;
surface remains smooth and shows pixelated/speckled foam. Not convincing
crest/froth realism, full shoreline stability or full collision validation.
Images: staged Saved/Screenshots/breaking-gate-staged-20260924_000..011.png.
Log:tmp/breaking-gate-staged-render-20260924.log. No further work was live when
the checks completed. South Fork and the complete ordered queue remain open.
