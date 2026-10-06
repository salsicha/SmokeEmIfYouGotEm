# Conservative bank contours in actual render coordinates

September28 UTC. Qualified candidate construction, **not normal playable
integration or river acceptance**. v26 remains the last delivered game and
still fails both rapid performance gates. No game package, captured source,
terrain, collision, cooked field, material or physical solver was changed.

## What this step establishes

The current normal render packet casts CPU FVector positions to FVector3f in
RaftSimShorelineMeshComponent.cpp. A certificate for ideal local or binary64
world points does not automatically survive that conversion. The new
RaftSimStoredBankContour candidate applies the storage conversion BEFORE its
whole-triangle and dry-band certificates. RaftSimThreeWetBankContour now takes
a storage policy; its original local-coordinate entry point remains available.

The policy uses an explicit render origin. Source subtraction must be exact
(error-free TwoDiff checks it), source buffer positions must be representable,
and every submitted point is binary32. The inverse-map intervals enclose the
exact stored buffer coordinate under the unchanged physical cell transform.
An independent Fraction audit reconstructs buffer + render origin exactly;
it does not trust the native rounded local inverse or native success flags.
Physical bed and depth values are never clamped, lifted or altered.

The same original captured v22 bank was checked in five frames: the original
physical location with a local storage origin, a translated control, two
reflections, and the original WHOLE-GRID origin. For the latter, dry source
26184 is row116/column84 in the225-wide captured grid. The common render origin
is(-551000,-348600)cm; the bank remains at(-542600,-360200)cm. The audit derives
that origin from the protected capture's IDs and field coordinates. This does
not independently survey the bed: these are the same cached hydraulic inputs
used by the earlier reconstruction diagnostic.

Four frames require67 boundary segments/69 wet triangles. The whole-grid frame
requires68 segments/70 triangles. Every actual stored triangle is exactly
certified wet, the omitted area outside the band is exactly certified dry,
and the band remains at most0.1cm. Exact edge incidence, radial/band ordering
and total cell partition are checked. Native ordering predicates prevent a
storage policy from accepting reversed/overlapping radial spans. Shared edge
points use the same semantic wet/dry crossing policy qualified previously.

## Retained failures and limits

The first build failed on a mixed-type auto declaration in the new test; that
declaration was corrected. Direct world-coordinate storage then failed the
whole-contour test in v2-v4; the other16 regressions passed. Those receipts and
logs remain. Rounding both coordinates outward is not generally wetward: the
captured contour has a negative X derivative near its fold. One retained
counterexample is wet at(46/1600,468/3200), but dry at(47/1600,468/3200).
The exact audit's regression retains this counterexample.

The policy now checks a bounded neighborhood of representable points, with
proved wet outer and dry inner endpoints, followed by full segment/triangle
proofs. Even that direct-world variant remains rejected on the captured bank;
it is explicitly tested as NOT safe. Rebased storage passes without widening
the band or substituting new donors. This is evidence for the rebased candidate,
not a proof that no possible direct-world algorithm could work.

Per-cell rebasing must NOT be used as the normal integration: neighbors could
round shared positions differently. The whole-grid frame test addresses the
candidate arithmetic but does not yet change the actual renderer. The renderer
must publish the SAME frame to raster, ray tracing, shoreline construction and
the corresponding inverse mapping, with explicit motion-history handling when
the frame changes. General sheared/non-Cartesian maps are rejected, not certified.

Construction is still milliseconds PER BANK, not a solved frame budget. v7's
whole-grid fixture took2.639700ms once; earlier v5 samples were about5ms. These
single native fixture timings are neither isolated game FPS nor a causal
optimization comparison. Do not enable repeated full reconstruction over
hundreds of banks every frame on the strength of these passes.

## Authoritative evidence

- Recipe: tmp/verify-stored-bank-contour-v7-20260928.ps1.
- Receipt: tmp/stored-bank-contour-v7-20260928-process.json, terminal
  native_and_exact_candidate_complete,2026-09-28T14:23:26.7269171Z.
- Editor build48.04s, exit0. Native17 tests PASS; zero warnings, failures,
  not-run or in-process tests.30 frozen implementation/proof/capture inputs
  rehash unchanged, including the protected user surface test.
- Independent exact audit: all five complete stored geometries PASS.
- Audit controls:15 tests PASS, including translation omission, GPU conversion,
  triangle/index/partition defects, band violations and the captured fold.
- Native export: tmp/stored-bank-contour-v7-20260928-stored.json;
  SHA25696b077dd4bb9d9926c8b77c84e5fc7e87c6d4ec52eee0d904fe1d5c871432a66.
- Exact audit: tmp/stored-bank-contour-v7-20260928-exact-audit.json;
  SHA2568d84e1eb80ad12352b6946bbd8b7685333598d18b7ab2796dab1646ab4375e3d.
- Original contact SHA256 remains
  bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f.

## Next integration, not an acceptance waiver

1. Implement a common published render-coordinate frame, covering raster,
   ray-tracing transforms, moving-grid history and unchanged CPU support.
2. Make canonical edges, the variable bank polygon, transported attributes
   and crest weights use that same frame. Stored triangulation connectivity,
   not only node count or winding, controls cache invalidation.
3. Avoid per-frame expensive recertification only with a mathematically valid
   cache domain. For fixed bed, the physical numerator is monotone in each
   positive donor depth; a proved lower-depth wet/upper-depth dry box could
   permit exact membership checks. This is a proposed next implementation,
   not an implemented/qualified optimization or permission for stale geometry.
4. Measure actual construction frequency and whole-update cost on both rapid
   captures before normal enablement. Rebuild into a fresh stage; never cook
   into the hard-linked v25/v26 stages. Verify Boot/menu, real motion/contact,
   shoreline continuity, raster/ray consistency and isolated20FPS/bridge-clock
   gates. No diagnostic pass here supplies any of those acceptance results.

## Common render-frame candidate and actual engine review

September28 UTC: a production-component implementation is now tested behind
-RaftSimRebasedShoreline. It is NOT enabled by default or delivered in a new
package. The CPU source mesh, support queries, collision and hydraulic field
coordinates remain unchanged. Only the GPU position buffer is translated by
one published whole-grid XY origin, not independently per bank.

The render-thread upload owns the origin and vertex payload together.
Raster primitive uniforms, local/pre-skinned bounds and ray-instance transforms
use the same helper. World bounds and actor position remain physical. Because
the vertex factory has only the current position stream, both current and
previous component matrices undo the CURRENT packet origin: substituting the
previous grid origin would introduce false motion when the grid moves.
Color, normal, tangent, four UV channels and index order remain unchanged.
The zero-origin reference retains its old conversion and matrix path.

Native qualification is terminal in
tmp/water-render-frame-v1-20260928-process.json:

- Editor build152.47s, exit0;20 native tests PASS, no warnings/failures/skips.
- The new test covers three origins, reflected/scaled/rotated component
  transforms, serial/parallel packet identity, all non-position attribute
  bits, dry packets and shifted local bounds.
- The earlier five complete stored-contour proofs and15 rejection controls
  still pass. All32 frozen inputs rehash unchanged, including the user-owned
  surface test. This does not integrate the conservative contours yet.

The actual editor -game run, using the same Boot/menu launch hierarchy, then
captured the8310 rapid with the candidate flag and a bounded upload audit.
tmp/water-render-frame-live-v1-20260928.json is terminal at14:43:01Z.
Boot/main-menu/FullReach/post-travel600-frame capture ordering passes;
both launch and motion logs contain zero runtime Error/Fatal lines.
The80 station samples move8312.897 to8486.898m (174.001m).

Across64 actual compact upload packets, maximum restored XY storage error is
0.001074810243205717cm, versus0.03491352909829735cm for direct world-to-float
conversion of those SAME source vertices. This is a CPU audit of the actual
submitted buffer values, not a numerical GPU transform readback, physical
survey accuracy claim or proof of wet containment for existing legacy contours.
At the near-origin menu start, rebasing need not improve direct-float error;
the measured candidate still satisfies the0.005cm storage guard.

One paired-detail support snapshot has1854 wet probes,160 ground-occluded dry
probes, zero unavailable probes and zero ground-occluded wet probes. Recomputed
probe classifications agree with every summary count. Maximum CPU support
versus submitted carrier error is0.000047670437652413966cm (guard0.001cm).
All18 emitter anchors pass their6/3/3cm clearances. Neither check establishes
particle landing, complete collision traversal or GPU detail sampler parity.
The actual log explicitly says hardware ray tracing is disabled by project
setting r.RayTracing=0: the common ray transform is wired and native-tested,
NOT exercised in this capture. No setting was changed just to claim coverage.

Original engine video:
unreal/Saved/VideoCaptures/RaftSim_20260928-074132.mp4,
SHA256ea30e03b04d9f2af27e10911425543ec12c3d199ec7354ed8e8053263e14a665.
Decode: tmp/sf-render-frame-live-v1-decoded-20260928/report.json,
2493 frames,0..83.066667s,1280x720,40 exact adjacent duplicates.
All seven requested stills exist;6/20/80s were inspected, with the prior v26
20s view as context, not a synchronized pixel comparison. Water remains
visibly aligned with raft/banks during rapid-to-calm travel. Broad flat foam,
weak breaking relief, coarse banks and crew fit remain unresolved. These
views cannot prove every shoreline edge or sub-millimetre rendering alignment.
Final review: tmp/water-render-frame-live-v1-review-20260928.json.

No isolated timing run was performed: recording and per-vertex auditing add
work, and encoded video rate is not gameplay FPS. The unchanged20FPS,
p95<=50ms, zero frames>100ms and bridge-clock gates remain open. v26 remains
the last normal package; its rapid gates still fail.

Next qualify this bounded render-frame change's actual publication cost and
normal-path configuration, then promote it into a fresh normal build once safe;
do not wait for the entire river to be perfect. Shared certified edges/full
contours, variable attributes and ear-connectivity cache identity remain
separate follow-on integration. Never cook into the immutable linked v25/v26
stages. No solver activation, source replacement, deletion, push or river
acceptance occurred. All native/runtime/decode owners are terminal.

## v27 normal playable delivery

September 28 UTC: the common whole-grid GPU frame is now the NORMAL path.
RaftSimLegacyShorelineCoordinates is an explicit diagnostic override; no
RaftSimRebasedShoreline opt-in is needed. Both actual packaged launch logs
confirm WATER_RENDER_FRAME_MODE rebased=1 legacy_override=0.
This supersedes the candidate-only status above, not its limits or failures.

The normal configuration passes all 20 native tests without an opt-in, plus
15 audit rejection controls and all five exact stored-contour cases.
tmp/water-render-frame-v2-20260928-process.json is terminal. CPU geometry,
source data, support, bed, collision and the solver are unchanged. The certified
full bank contour still is NOT integrated by this precision-only delivery.

The standalone build succeeded in 135.51s. The fresh stage is
tmp/south-fork-playable-v27-20260928/Windows; binary SHA256
82e139184dbd93c46ebf7c0419e49da850db003d0aab4071ac35bba5dd65bcd0.
tmp/water-render-frame-v27-20260928-package.json records 36 frozen inputs,
3,106 immutable dependencies linked from verified v26, independent executable,
PDB, manifests and Saved outputs. Runtime closure verifies 2,405 files,
917,995,570 bytes, with no external fallback. This was a code-only build,
not a cook or a reduction of the full-copy disk-space gate. Never cook into
the linked v25/v26/v27 stages or overwrite inherited dependencies.

Normal Boot/main-menu/FullReach travel and post-travel capture ordering pass.
The rapid's 80 motion samples cover 8313.432 to 8484.122m (170.690m).
Both logs are free of runtime Error/Fatal lines. The support snapshot contains
1,859 wet probes and 155 ground-occluded dry probes, zero unavailable probes,
zero ground-occluded wet probes, and maximum support/carrier difference
0.0000476705340588524cm. All 18 emitter anchors pass. These remain bounded
CPU support/source-anchor checks, not GPU sampler readback, particle landing
or complete swept-collision acceptance.

The actual engine clip contains 2,483 frames over 82.733333s at 1280x720,
with 36 exact adjacent duplicates. All seven requested stills were decoded;
6/20/80s views were inspected. Raft and water remain visibly aligned from
rapid to calm water. Broad flat foam, weak breaking relief, angular banks
and crew fit are still present. No new macroscopic breaking shape, full
shoreline stability or geographic acceptance is claimed.

- Runtime: tmp/water-render-frame-v27-motion-20260928.json.
- Video: tmp/south-fork-playable-v27-20260928/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260928-075600.mp4.
- Video SHA256:85dbba622f2b16cd5c4f58600d278a856dd336524a32b70305254ab083f51b3d.
- Decode: tmp/sf-v27-motion-decoded-20260928/report.json.
- Isolated profile owner: tmp/water-render-frame-v27-profile-20260928.json,
  terminal 15:01:56Z. No other game, build, cook, source replay or decoder.
- Per-run frame receipts: unreal/Saved/RaftSimValidation/sf-v27-isolated-{menu,8310,11520}-20260928-frame-audit.json.
- Strict scopes/clock: tmp/sf-v27-isolated-{menu,8310,11520}-20260928-scopes-and-clock.json.
- Final scoped delivery/integrity: tmp/water-render-frame-v27-final-review-20260928.json.

All timing runs use 1,200 actual frames and audit rows 30..1169, with the
unchanged 20 FPS / p95<=50ms / zero individual frames>100ms requirements.
Timing mode and default render-frame mode are confirmed in each engine log;
no record/audit/candidate flag or quality/solver override is used.

| Normal setting/start | Mean ms | p95 ms | Max ms | Frames >100ms | Timing gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot/menu | 37.9089 | 44.8092 | 59.1377 | 0 | Pass for this sample |
| 8310 rapid | 44.4600 | 62.6842 | 181.8656 | 8 | FAIL |
| 11520 rapid | 65.9468 | 87.4577 | 182.9282 | 4 | FAIL |

At 8310, bridge backlog is 0.8810 to 0.015554s, with 178 four-tick rows.
At 11520 it is 0.9309 to 0.7768s, peaking at 5.5403s; 1,100 of 1,140 rows
consume four ticks. Neither is simulation-capacity acceptance. No elapsed
water time was discarded or fixed step increased.

The heavy run remains CPU-bound: mean game thread64.0552ms vs GPU19.8361ms.
Surface Tick40.0050 includes CartesianPublish23.3943, SetMesh22.0563,
crest Update14.2755 (Selection8.4221), and topology6.3454ms. These are nested,
not additive. Solver StepWater14.3298ms is separate. Deferred RenderPacket
averages0.40175ms across all rows,1.99128ms on positive rows (p952.7675ms);
at8310 it averages0.11388ms,0.78684ms on positive rows. These are actual
normal-build costs, not same-input reference/candidate deltas. Cross-run
trajectory/timing variation prevents claiming a causal FPS improvement.

This completes the bounded normal-path precision delivery, not South Fork.
Next integrate shared certified crossings and variable full contours with
correct attributes/crest weights/ear-connectivity cache identity, qualify
reuse cost, and continue physical breaking/recirculation and publication-cost
work. Hardware ray tracing remains disabled by normal project settings:
the common transform is wired/native-tested, not hardware-exercised here.
Preserve the rejected solver state and all retained evidence; no push.

## Integrated candidate and real-grid rejection

September28 UTC: common certified edge coordinates and complete variable-size
three-wet bank contours now feed the real shoreline builder/cache behind
RaftSimCertifiedBankContours. This is NOT enabled by default and is NOT a new
normal playable delivery. v27 remains the normal packaged game.

The integration preserves original donors, shared lattice edge identity and
the certified triangulation itself. Variable contour fractions transport UVs
and crest weights; changed node counts or triangle connectivity rebuild the
cache. Candidate updates are transactional: rejected geometry leaves the
previous successful mesh/cache intact. Full-cache/mesh copying is deliberately
candidate-only and still requires cost reduction before promotion. Neither
retention of old geometry nor process exit zero constitutes acceptance.

The initial native build failed on a float3-to-double2 test conversion. After
write access recovered, that conversion was fixed. Preserved receipts v2..v5
are terminal. The latest is
tmp/certified-bank-integration-v5-20260928-process.json:20 native tests,
15 independent audit controls and five exact stored-coordinate proofs pass.
Native comparisons bind actual submitted base-bank XY and every triangle to
the independent certificate; unchanged input reuse and rejected-frame rollback
are tested.20 additional depth/orientation updates cover all four dry corners,
16 node-count rebuilds and equality against fresh builds. Zero same-size ear
changes occurred, so that specific dynamic coverage remains outstanding.
The captured live rejection below is intentionally a negative regression;
its passing test does NOT mean the candidate is safe to ship.

Three bounded engine runs used actual South Fork FullReach at8310, the normal
rebased render frame, six motion samples and no solver override. The first
run (tmp/certified-bank-smoke-v1-20260928-process.json) exited successfully
and moved8311.820..8316.895m. Its first/last screenshots were inspected:
water/raft alignment remained visible, while weak breaking, coarse geometry
and crew fit remained unresolved. That run lacked per-publication acceptance
telemetry, so it could not detect stale mesh retention and is superseded by
the instrumented failures below. It must not be cited as continuity acceptance.

Component diagnostics now emit an error on rejected candidate publication,
with optional RaftSimCertifiedBankAudit construction cost and exact failing
cell data. The v2/v3 engine runs both failed their runtime health checks,
despite process exit zero. Latest log:
tmp/certified-bank-smoke-v3-20260928.log, SHA256
dd457420acec052138fcc7cd50ca656e59c8ed99eb0fbcd0702d2b3f2166273a.
All frozen implementation inputs were unchanged during each run.

In v3,34 updates succeeded and44 rejected; the first rejection is frame34,
source31556, dry corner0, certificate boundary-construction stage1. Exact
bed/depth/coordinate values are retained in
[the captured rejection fixture](certified-bank-rejection-31556.json).
The failed local endpoints are approximately(0.0000048828125,0.001494140625)
and(0.0000048828125,0.001484375). Equal quantized X and decreasing Y reverse
their order around the dry corner; the strict partition predicate correctly
rejects that span. This identifies a storage-selection defect, not permission
to remove ordering checks or widen the1mm geometric band. These captured values
are simulation inputs, not newly surveyed bathymetry.

The34 successful topology calls have median54.435702ms, range17.676..454.876602ms;
31 exceed50ms. These include startup, near/far components, capture and audit,
and are NOT isolated full-frame timings or a causal comparison with v27.
They rule out treating this candidate as performance-qualified. No physics
time is dropped and no quality/performance gate is relaxed.

Next fix stored-point selection/order using the reproduced cell, then replace
the negative control with full positive native and independent exact proofs.
Qualify construction reuse and transaction cost, same-size ear-change coverage,
actual post-crest stored geometry, long-motion/contact/shoreline stability and
isolated frame/bridge-clock cost before normal delivery. Do not recook or
overwrite the immutable linked v25/v26/v27 stages. No known broken solver was
enabled. No source data was removed, no river accepted and no push performed.

## Partition-bound repair and bounded engine replay

September28 UTC, superseding the previous unresolved-negative-control status.
The failed reversed quantized spans were real and correctly rejected, but
further isolation found that they arose after excessive subdivision driven by
false partition bounds. Two defects were reproduced: independently rounded
inner points could sit across their outer ray, and Cross(P,origin,origin) lost
the exact repeated-vertex dependency during interval multiplication.

The repair selects an actual binary64 inner point conservatively against the
same partition expression, with correction computed from the interval deficit.
Cross returns exact zero only when two vertices have identical singleton
coordinate bounds. Uncertain overlapping bounds do not qualify. No epsilon,
donor change, coefficient clamp, ordering bypass, enlarged band or removed
wet/dry/partition proof is used. The failed midpoint-search and sorting trials
were removed, not silently shipped. Both original and failed-trial logs remain.

Progressive native/replay trials matter: v5 proved the original frame34 state
but live-v1 rejected at frame66; v6 proved that later state but live-v2 rejected
at frame80. v7 sorting still failed native case7. Only v8 includes the exact
repeated-origin repair and passes all20 native regressions,15 independent audit
controls and eight exact whole stored-coordinate cases. Cases5/6/7 bind original
donors to immutable source31556 raw logs at frames34/66/80, respectively:

- tmp/certified-bank-smoke-v3-20260928.log:
  dd457420acec052138fcc7cd50ca656e59c8ed99eb0fbcd0702d2b3f2166273a
- tmp/certified-bank-ordering-live-v1-20260928.log:
  709e34f3bd58baab49850200e2e2c0fe8c6d6aaddda186a116163c3ad6dcff88
- tmp/certified-bank-ordering-live-v2-20260928.log:
  6293eed8a9114af3889ed27ed2113f96627285e782dc08c447ff5f80416dde89

Each captured case now has five boundary segments/seven GPU triangles, with
native real-builder/cache/attribute comparison and independent exact wet/dry,
partition, float-coordinate, shared-edge and maximum1mm-band certification.
65 additional float32 synthetic depth samples between the first/last capture
pass native full certificates. They are not measured intermediate hydraulics
or a proof of the continuous range. Prior20 orientation/depth updates remain;
same-size changing-ear dynamic coverage is still outstanding.
Native receipt: tmp/certified-bank-ordering-v8-20260928-process.json.
Stored export SHA256 c33026993b8a3f3fbacdf13525dd903ca90d0487e0fd23da4ff2a1b8b9887995;
exact audit SHA256 be2a30c166ab962601d1273e3482231b328a640e62621eaa07a556649cd26dae.
All frozen inputs, including the protected automation test, are unchanged.

One fresh actual FullReach8310 replay, ordering-live-v3, exercised the candidate
with the normal rebased render frame and no solver override. It exited zero,
reported180 accepted updates and zero rejected updates/runtime errors, and
recorded20 motion samples from8312.359 to8335.768m (23.409m). First/last actual
1280x720 engine screenshots were inspected: gross water/raft alignment remains,
while broad flat foam, weak breaking, coarse banks/rocks and crew fit remain
unaccepted. This is a short still-series motion run, NOT continuous animation,
long traversal or full shoreline-stability acceptance. Screenshots:
unreal/Saved/Screenshots/certified-bank-ordering-live-v3-20260928_000.png and
_019.png. Runtime receipt: tmp/certified-bank-ordering-live-v3-20260928-process.json;
log SHA256 c95c2d053ae9f16532dae068fcc261a05b811a457bea2e9832b6fcf650eedc6b.
At world10.09126s the independent submitted-triangle contact audit reports1870
wet points,143 ground-occluded dry points,zero unavailable/ground-occluded wet,
maximum support/carrier error4.7664964768e-5cm. GPU upload parity is separate
and was not requested by this run.

The180 diagnostic topology calls have median48.838949ms, mean60.6665015ms,
range3.631998..334.412698ms;58 exceed50ms. Startup, near/far components, audit
and screenshots are included. These are NOT isolated full-frame timings or a
causal speedup comparison. Construction/publication cost still prevents safe
promotion; previous v27 rapid20FPS/bridge-clock failures remain unresolved.
Candidate flag stays OFF by default; v27 remains the delivered normal game.
No cook, package, solver activation, data deletion, river acceptance or push.
Native and engine owners are terminal. Next qualify cheaper construction/reuse
without relaxing proofs, cache/ear changes and actual post-crest geometry,
then longer motion/contact/rendered shoreline and isolated frame/clock cost.
