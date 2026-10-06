# Ordered parallel crest triangle emission

September28 UTC. This reduces CPU mesh-construction work while preserving the
existing water shape; it is not new breaking-wave physics or visual acceptance.
The v25 heavy-section failure motivates this work: p95102.1761ms,74 frames over
100ms and15.3877s of added bridge backlog. All acceptance gates remain unchanged.

## Implementation and exact qualification

The original serial midpoint pass still assigns every vertex ID in the same
order. For levels with at least2048 triangles, independent workers classify each
triangle's split edges and green diagonal from immutable data. A prefix pass
allocates exact child/green-metadata ranges; workers fill disjoint ranges in
original source/child order. Midpoint parents, triangle indices, ownership and
the ordered metadata governing later topology reuse are unchanged. Workers
join before any arrays are reused. Small levels retain serial emission.

Normal `FRaftSimShorelineCrests::Update` now enables this qualified path.
`RaftSimSerialCrestEmission` is the explicit original-path diagnostic control.
The new `RaftSimParallelCrestEmissionAudit` compares independent stateful builds
on identical actual inputs, alternates timing order, checks full ordered outputs
and production topology, and never publishes its diagnostic mesh. It also
requires the parallel path to have executed; no empty-path success is accepted.

Initial editor build300.94s and15 rendered native tests PASS, zero warnings,
failures, skipped or running tests. New coverage includes all eight edge masks,
rotations/winding, both green diagonals,96 full adaptive builds,138224 expanded
coordinates,68 parallel assembly levels and116 cache reuses. Both original and
indexed edge maps and compact/retained storage are tested. Post-normal-integration
editor build15.06s repeats all15 tests successfully,21 frozen inputs unchanged,
including the protected user water test. Receipts:
`tmp/parallel-crest-emission-{v1,v2}-20260928-process.json`.

Two live captures each contain64 exact pairs after two warmups,32 pairs in each
order, zero runtime errors and exit0. Whole adaptive-build means (not FPS):

| Capture / order | Serial ms | Parallel ms |
| --- | ---: | ---: |
|8310 serial-first|14.755282|12.593812|
|8310 candidate-first|15.058612|12.414360|
|11520 serial-first|12.102897|9.047254|
|11520 candidate-first|12.243203|9.062635|

At8310,143 levels use parallel emission and expanded meshes range33116-36396
vertices; at11520,195 levels and32648-34668 vertices. All128 pairs preserve exact
coordinates, ordered parents/indices/owners and cache build/reuse decisions.
Terminal receipt `tmp/parallel-crest-emission-live-v1-20260928-process.json`.
Report hashes:

- 8310: `c82febf06901766be1061935e090a10d95389a3177bb2ff756a498c2443886df`
- 11520: `cfe99227ab2f236a907f69ea61fc12c044b635cea70014165ae736dd80a7f825`

## v26 code-only staging and preservation

The standalone Development game build succeeded in214.45s. Only C++ behavior
changed; existing cooked assets and source-bound runtime payloads are reused.
A separate stage `tmp/south-fork-playable-v26-20260928/Windows` has its own new
executable, symbols, generated manifests and writable Saved output. Its3106
unchanged dependencies are verified hard links to v25. **Never cook into either
linked stage or overwrite inherited files.** Future cooks must use fresh stages.
No source, package or evidence was deleted. v25's executable remains unchanged.
The14GiB full-copy staging gate was not lowered or used: this was a code-only
build/link stage, with a separate6GiB build/copy headroom check, not a full cook.

The first link attempt failed on a286-character path. The first recovery then
exposed a UTC-reparse bug in its timestamp guard; the build file was correctly
newer than build start. Both failed receipts are preserved. Recovery2 uses
extended paths and retains DateTime kind, verifies already-created links, and
reuses the SAME successful build without recompilation or deletion.

Authoritative terminal receipt:
`tmp/parallel-crest-v26-20260928-package-recovery2.json`, completed13:30:57.3877663Z.
Staged closure verifies2405 runtime files/917995570bytes with no external fallback.
All frozen inputs and original baseline dependencies remain unchanged.
New binary SHA256: `98bb23fde30702081f03aefe8e2d4fbafc19302be2fc2f95281bed9406027bc6`.
Linked inventory `tmp/parallel-crest-v26-20260928-linked-files.json` SHA256:
`032fee4da91ca898df1851403278f7b0158dd3808d907c8f6679c5b69177d0b4`.

## Normal runtime and actual motion

Normal Boot -> main menu -> FullReach ->600 post-travel frames passes in order.
A separate8310 diagnostic placement on the normal playable map records80 motion
samples from8313.076 to8487.396m (174.320m). Both game owners finish0, no runtime
Error/Fatal entries, unchanged25 frozen inputs and binary. Receipt:
`tmp/parallel-crest-v26-motion-20260928.json`, completed13:33:56.6827656Z.
This is delivered normal-path CPU work, not merely an editor/command-line opt-in.

Contact audit:1869 wet probes, maximum support/carrier error0.000047653142132730864cm;
159 raw-dry probes all counted ground-occluded, zero unavailable or
ground-occluded-wet probes. The stride sample does not clear every historical
location, full-shoreline continuity or complete collision acceptance. All18
sampled emitter centres pass6/3/3cm clearances; particle landing is not proved.

The original82.666667s recording fully decodes2481 frames at1280x720,33 exact
adjacent duplicates, with all seven requested review frames present. Video:
`tmp/south-fork-playable-v26-20260928/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260928-063229.mp4`.
SHA256 `26883f1e0090e75bb2adf8ffb1783c63117dd9158e00663558fd2b2bc1dc01cc`.
Decode receipt/frames: `tmp/sf-v26-motion-decoded-20260928`.
Reviewed6/20/80s views show the raft progressing through the rapid into calmer
water, but broad flat foam, weak breaking, coarse banks/boulders and crew/paddle
fit defects remain. Neither recorded frame rate nor stills prove FPS/animation.

After gameplay, all3106 inherited files were independently rehashed in BOTH
stages, with both binaries and25 frozen inputs unchanged. Receipt:
`tmp/parallel-crest-v26-post-runtime-integrity-20260928.json`.

## Isolated frame cost and bridge clock

All build/game/decode/integrity workloads ended before sequential1200-frame
profiles. Each audits1140 rows30..1169; same binary, normal graphics/solver
settings, no legacy/quality overrides, runtime errors0, exit0. The review
stations are diagnostic placements, not claims about normal menu spawn location.

| Launch | Mean ms | p95 ms | Maximum ms | Frames >100ms |20FPS timing gate|
| --- | ---: | ---: | ---: | ---: | --- |
|Boot/menu|39.3032|46.4228|58.5586|0|PASS for this sample|
|8310|46.4601|66.6790|184.5757|6|FAIL|
|11520|66.1613|86.3125|200.2795|3|FAIL|

Receipts: `unreal/Saved/RaftSimValidation/sf-v26-isolated-{menu,8310,11520}-20260928-frame-audit.json`.
Strict independent CSV/scope/clock reports:
`tmp/sf-v26-isolated-{menu,8310,11520}-20260928-scopes-and-clock.json`.
Actual logs confirm `csv.UseLegacyFrameTime=false`, supporting offset1 scope
alignment. Only the actually duplicated unmeasured engine counter is exempted;
no measured columns, frame rows or failures are removed.
CSV hashes respectively:

- menu: `5a76461ecc47a2427ac71b2a6aeb4d1c7d282efdfc5e5907bd91095eeb8875bc`
- 8310: `651bf4387eaacf798b422a8906eb271aa5913a8683eec6d9d0c81cc644eec449`
- 11520: `59b1a1cfe242b5345a9810d6929b3e2ef21df83cd71a8938ef1b305b69b20e51`

Bridge backlog: menu0.007015->0.004548s (max0.016612s);8310
0.883100->0.011220s (max0.886900s);11520 0.990700->0.391000s,
but max4.604600s and all1140 rows still at four fixed ticks. Heavy-section
requested time advances75.3336s, committed time75.9333s, paying down0.5997s
of prior debt. This does NOT establish sustained simulation capacity: all
capacity-acceptance flags remain false. No elapsed time was dropped or dt changed.

Heavy-section mean GameThread64.2051ms, GPU19.3199ms. Surface Tick40.1331ms
contains publication23.6292ms, SetMesh22.2820ms, crest Update14.3548ms,
Selection8.5165ms and topology6.4611ms. StepWater14.3957ms is separate.
Never sum nested scopes. The new heavy sample is better than v25's mean80.1968ms,
p95102.1761ms/74 hitches and16.7611s final debt. These different trajectories
are NOT a controlled causal whole-frame speedup; only the paired adaptive-build
timers above have identical inputs. Both rapid gates still fail.

All owners are terminal; no live cook/build/game/profile remains. No push.
South Fork stays open. Next address coherent three-wet shoreline integration
and actual physical breaking/recirculation, alongside remaining CPU publication
cost, collision/animation and sustained timing/clock validation. No broken solver
was enabled and no gate was weakened. Colorado and later rivers remain queued.
