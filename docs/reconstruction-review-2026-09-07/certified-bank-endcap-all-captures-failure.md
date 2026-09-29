# Expanded endcap coverage: native repaired, bounded replay passes

## September29 v9: stable-source replay passes, isolated timing fails

After external work committed at a8933516d and the engine became idle, the
single v9 chain completed (session56716 exit0). v9 qualified all21 native
tests,62 captured states,15 exact polygons and48 shared crossings. Its live-v3
replay passed90 samples from8311.820 to8393.458m,470 accepted nonempty bank
updates,zero rejects and unchanged input/binary hashes. Detail frame42 passed
4226 GPU queries with maxRGBAerror1.49e-8;1912 wet support probes had zero
unavailable or ground-occluded wet points. These remain bounded checks, not
whole-river, swept collision or visual acceptance. Video:
`unreal/Saved/VideoCaptures/RaftSim_20260928-221500.mp4`, SHA256
`6a69e308f17b66d6f4b4356184209b435302be209733225b061e44032db839a0`.

The subsequent actual Boot/menu candidate profile, without capture/audit
overhead, ran1200frames and audited rows30..1169. There were no runtime errors,
source/binary changes or competing workloads. It FAILS20FPS/50ms p95 and the
zero-hitch gate: mean62.796ms,p95102.2014ms,max442.031ms,67frames above100ms.
Receipt: `unreal/Saved/RaftSimValidation/sf-certified-endcap-v9-menu-20260929-frame-audit.json`.
Original CSV: `unreal/Saved/Profiling/CSV/Profile(20260928_221714).csv`, SHA256
`7d610cb1babee70e79d445d55dfa9ca355318392b4af4fcb4fb25f6c002cbb37`.

Inclusive scope means: surface Tick40.179ms,CartesianPublish27.504ms,
SetMesh26.677ms,Topology21.144ms,Refresh12.083ms,StepWater11.795ms. Topology
p95 is52.508ms. Nested/thread timings cannot be added or treated as an exact
causal partition. GPU mean19.238ms and p9534.918ms; game-thread mean62.588ms.
Bridge debt starts2.5343s,ends2.0145s,reaches5.7572s, with945 of1140 frames
running the4-tick limit. Zero failed solver frames is NOT capacity acceptance.

The next justified work is certified contour/update cost reduction with all
wet/dry/width/storage/orientation gates retained. No need to repeat unchanged
v9, no candidate promotion, no new normal playable build or commit. Appearance
and full physical/geographic acceptance remain open. Earlier ownership
blocker below is historical; the stable validation window succeeded this run.

## Current validation ownership blocker

v8 native/exact qualification passes21/21,62/62,15 polygons and48 crossings.
Its follow-on live-v2 engine exited0, but concurrent
`RaftSimEditorLandscapeFoliagePlacement.cpp` edits invalidated the post-run
source check. Video is preserved at
`unreal/Saved/VideoCaptures/RaftSim_20260928-200526.mp4`, SHA256
`4cf166ab42e858475f3acc0e60dbda7fdd239f22edbe457ca583ec10e29d8813`.
This is not a qualified v8 replay or current-tree acceptance. Menu profiling
never launched. Session77378 terminal1; no remaining owned validation process.
Repeated source churn now requires an exclusive validation window or isolated
checkout; do not silently relax the source/binary gate or keep rebuilding.

### Video review and subsequent qualification drift

Decoded2970 frames from the actual v7 replay,0..98.9667s, with269 exact adjacent
duplicates. Recording frame rate is not engineFPS. Decode report/stills:
`tmp/certified-bank-endcap-transition-live-v1-decoded-20260929/report.json`.
Inspected20/60/80s boat-camera images show advancement past right-bank rocks
and changing surface texture, but broad flat white foam patches, weak breaking
relief and coarse angular banks/boulders remain. These separated views do not
prove temporal shoreline stability, crew animation or whole-surface continuity.
No visual acceptance follows from the passing bounded topology/contact checks.

The v7 menu profile never launched: its source gate found subsequent concurrent
`RaftSimSurveyCommand.cpp` changes to use the scenario run/progress axis in
Cartesian-map surveys. v7 replay stays valid for its tested state, not new
current-tree performance. Preserve that other work. Fresh v8 qualification,
v2 replay and menu-profile chain is queued under exec session53422, with all
gates retained and an explicit qualification-receipt hash binding the replay.

## September29 v7: qualified current source and bounded runtime pass

v7 (`tmp/certified-bank-endcap-transition-v7-20260929-process.json`) passes
21 native tests,62 original captured states,15 exact stored polygons and48
exact shared crossings with unchanged inputs. v5/v6 native tests also passed
but their concurrent source drift prevented qualification; do not reuse them.

The qualified candidate replay (`tmp/certified-bank-endcap-transition-live-v1-20260928-process.json`)
exited0, captured90 samples spanning85.066m, and reported491 accepted bank
updates with no rejects. All frozen source/binary hashes remain unchanged.
Actual video: `unreal/Saved/VideoCaptures/RaftSim_20260928-195320.mp4`, SHA256
`1311615be19dff2ac726ca8dad2d5ad81c871a8e3add0503bd88c3c0f9aa9b0f`.

Presented detail frame43:4226 GPU queries,maximum RGBA error1.4901161193847656e-8,
passed. CPU contact:1909 wet points,zero unavailable/ground-occluded wet points,
maximum support/carrier error4.759293790357333e-5cm. This proves one matched
detail upload/sampling/contact snapshot, not bank GPU topology, render latency,
swept collision, whole-river traversal or visual acceptance. The post10s
breaking-height rows were captured; their interpretation remains pending.

Visual review and isolated cost remain pending. Normal playable v27 and its
candidate-OFF setting are unchanged. No gameplay delivery or acceptance follows
from this diagnostic replay. Earlier pending/current-tree notes below are history.

## Current-tree requalification pending

The prepared replay additionally requests RaftSimDetailContactAudit and requires
the GPU report to pass its existing native1e-6 RGBA error bound with nonempty
queries and the exact same positive detail_frame_sequence as the CPU carrier
contact snapshot. Paired-detail inclusion and audit request must be true; wet
support must be nonempty with zero unavailable/ground-occluded wet probes.
Both report hashes and scope are retained. Existing contact artifacts prevent
reuse of the run identity. Syntax validation passes; this audit is NOT RUN.
This only checks one uploaded detail texture and its material sampling helper
against the simultaneous CPU payload, not GPU bank topology, latency, complete
swept collision or full traversal. The earlier shared-reserve contact receipt
explicitly had detail_gpu_audit_requested=false; its CPU pass cannot fill this
GPU evidence gap. No solver mode or surface geometry is changed by the audit.

The prepared replay now also requests the existing logging-only
RaftSimBreakingHeightAudit and retains its raw post-10s detector rows even when
later replay gates fail. Its syntax parses; it is NOT RUN. Missing rows are
missing evidence, and a single post-10s sample is not proof of settled flow.
The prior shared-reserve replay had only a startup ownership estimate
(strongest interior crest0.010m at frame1) and a later accepted-crest source
maximum0.833866715; these are different measurements, not interchangeable
visible wave heights. No settled-height diagnosis or crest amplification is
justified from them. Reinspection of normal v27's20s image and the older
shared-reserve30s image still shows broad flat foam ribbons and weak visible
relief; those old images do not qualify the current candidate. The active
FullReach generator uses RaftSimFrothCells.ush, not the older captured-optics
HLSL. No material or hydraulic parameters were changed during this inspection.

After v4, the frozen-input check detected three changed editor files:
RaftSimEditorMaterialsBase.cpp, RaftSimEditorEnvironmentInternal.h and
RaftSimEditorEnvironmentCatalog.cpp (Zambezi upper-gorge support). All17
compiled binaries still match; v4's passing results apply to that tested
binary, not the now-changed source tree. These other-owner edits are preserved.
Only our obsolete replay-wait wrapper40824 was stopped; session19321 exited-1
without launching the candidate. Cook41272 remains live. Session47600 waits for
it before one guarded v5 build/native/exact requalification. Do not duplicate
the wait or bypass the source/binary gate. The v4-bound live/profile recipes
remain unrun and require rebinding after a successful current-tree gate.

## Witness-only v4 qualification — September29

The singleton endcap correction is now applied. A close proved dry witness is
retained when no additional representable GPU row fits; no outer strip is emitted
for First==Last. The unchanged width, depth and final partition gates remain.
The exact frame399 partial construction regression passes, including negative
controls for the old reversed fan, extra vertical row and naive radial next
witness. All four supporting shallow-endcap tests pass.

The editor build succeeded in198.33s. v4 passes21/21 native tests with no warnings,
including62/62 original captured rejection states through independent bounded
and full construction, actual cache publication and clockwise GPU geometry.
Exact audits certify15 stored polygons and48 crossings;17 audit controls pass.
The recipe verifies frozen sources and compiled binaries. Session14008 exited0.
Receipt: `tmp/certified-bank-endcap-transition-v4-20260929-process.json`.

This repairs the captured native correctness failures, not geographic, physical,
visual, runtime or performance acceptance. A new separately owned Zambezi w2
cook41272 is live. Session19321 waits on it before one v4-bound90-sample actual
engine replay with video/contact capture. The profile recipe also binds v4 but
remains unrun and requires successful replay. Candidate remains OFF for normal
play; normal v27 and protected WaterSurfaceTest hashes are unchanged. No commit
or push. Earlier failure/write-blocker notes below are retained as history.

## First-row native result and pending witness-only correction

September29 00:40 UTC v3 builds successfully in44.08s.20/21 native tests pass;
53/62 original captures now certify and publish clockwise geometry. Failures
389..398 are cleared. Remaining399..407 fail BOTH bounded and full searches
at stage1. Their diagnostic wet/dry proofs are true, outer order and both band
triangles positive, but the inner fan is negative. capX=0 and capY=0 throughout.
All728 frozen inputs match after execution. Session43131 exited1; native40128
exited255. No unchanged rerun, downstream exact audits or runtime replay.
Native log SHA256:
`3ddf537911db961971ae19e0c64ace70722787c80508ddaf12434fd8f95b86ec`.

Inspection identified the next repair: PrepareEndcap computes and proves a
close dry witness, but discards it when Last equals its first point (no extra
GPU row fits). InnerPoint then uses a distant normal witness that reverses the
next fan. Retain that one-point witness for its exact stored endcap; skip outer
strip emission for First==Last. Keep its width and original final neighboring
segment/partition proofs mandatory. This correction has NOT landed: two
scoped apply_patch attempts failed to write the header. The first attempt
terminated before creating a v4 recipe or launching any build. Read-only
diagnostics show Archive (not ReadOnly) and inherited Modify/Full ACL grants,
without a displayed deny. No ACL/config changes or permission workaround.

Another owner's cook38964 now runs Zambezi w0(60000steps). Preserve that cook
and captured inputs. The earlier waiting/preparation notes below are history;
no South Fork validation session currently remains live. Candidate stays OFF.

## Subsequent first-row connection repair (native validation pending)

Exact-rational checks reconstructed the actual binary32 XY from all19 failed
span records and certified every whole outer segment wet. This narrows the
failure to dry witnesses/partition rather than a dry connection interior.
For original frame389, edge=(487/10240,0), first=(5547/102400,1/102400),
second=(3097/51200,1/51200): edge-to-first and first-to-second certify wet;
first-to-second has a wholly dry inner fan and positive partition orientations
with rounded binary64 radial witnesses inside1mm. Edge-to-second is not wet.
The second-row direct-edge search therefore imposes an unnecessary chord and
pushes its endpoint beyond the radial dry band even though the consecutive
path can work. These are simulation captures, not surveyed river geometry.

FStorage now permits direct axis chords only for the first representable
off-axis row. Row-root proposals still cover near-axis rows, and every final
width/wet/dry/orientation/partition/triangulation gate is unchanged. The exact
partial-span suite now passes3 tests. This does not prove the full62 cases.
The native captured replay independently evaluates bounded/full searches and
reports proof predicates if either fails, avoiding the old short-circuit.

New validation recipe: tmp/verify-certified-bank-endcap-transition-v3-20260928.ps1.
It parses but is unrun. Exec session43131 waits on separately owned cook6808
(tmp/zambezi-cook-v1,36000steps) then invokes it once after ownership checks.
Resume that handle, do not duplicate it. Candidate OFF; normal game unchanged.

September29 2026,00:16 UTC. This is candidate diagnostic evidence, not playable
delivery or acceptance. Normal v27 remains unchanged and the candidate is OFF.

## Executed result

The existing Zambezi cook4460 exited; waiting session34149 then invoked the
prepared v2 recipe exactly once. Build succeeded in38.09s. Native process444
exited255, session34149 exited1. Neither process remains live.

- Native tests:20 succeeded,0 warnings,1 failed,0 unrun/in-process.
- `RaftSim.M4.StoredBankCapturedReplay`:43/62 original rejected captures now
  certify and publish matching ears with strictly clockwise submitted GPU faces.
- All19 remaining failures are frames389..407/source19466, at construction
  stage1, before cache or winding assertions. The other20 native tests pass.
- All728 frozen source/evidence hashes and17 compiled DLL/module hashes match
  after failure. This is not interference from another workspace edit.
- Recipe stopped at native failure: it did not execute its subsequent exact
  audits, new live replay, contact/animation review or isolated frame profile.

Receipt: `tmp/certified-bank-endcap-transition-v2-20260928-process.json`.
Native log: `tmp/certified-bank-endcap-transition-v2-20260928-native.log`.
Log SHA256: `2ca48fe997c983b5f7fc4eedc5c3a3b01fc534462555fcafb0450a9e45050f57`.

## Next repair boundary

First failing frame389 records adjacent proposals:

```
A=(0.060771484374999997,1.953125e-05)
B=(0.060488281249999998,1.953125e-05)
```

Other failed pairs move between the first, second and third representable
rows as the original captured depth changes. Stage1 means adaptive segment
construction exhausted its bound without satisfying its full interval gate;
the present log does not isolate the specific wet/dry/partition subcondition.
Do not infer that increasing a subdivision limit or sorting alone fixes it.
Repair the generic stored transition and neighboring dry-witness correspondence
while preserving every width, wet/dry, partition, ear and GPU winding gate.

The test's `full_stage=0` is NOT evidence of full-search success: its expression
short-circuits on the bounded build failure, so full search was not reached
for these19 records. Evaluate both independently if further diagnostics need
that comparison. Retain all62 original donors and render origins.

No new package/cook, solver activation, acceptance, commit or push was made.
Normal executable SHA256 remains
`82e139184dbd93c46ebf7c0419e49da850db003d0aab4071ac35bba5dd65bcd0`;
protected WaterSurfaceTest SHA256 remains
`d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3`.
