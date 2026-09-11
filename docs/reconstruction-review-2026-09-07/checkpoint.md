# Queued reconstruction checkpoint

The queue is active, not complete: **South Fork → Colorado → Pacuare → Futaleufu**. The existing hourly follow-up now works on South Fork instead of waiting for another task to complete it. Later rivers remain gated on playable reconstruction and physics validation.

## Completed in this pass

Latest continuation: prior user-status turn was informational; this pass made
code changes and gathered live GPU evidence. Build6053 terminalsuccess1104.07s;
incremental38222PASS11.12s. Newprofile test initially failed800vs799.9999999999999
computedextent; fixed double-arithmetic-roundoff comparison only, with altered
extent negative regression. Build95743PASS22.17s; engine-face-bed-source-v2,
session79198terminal0:14pass (1unrelatedHTTPwarning),0fail/RHI.301PythonPASS.
Dense exact-bed-flow-v2/session84596terminal0 capture is REJECTED atstep30
`[0,64,718008,54]` (120steps/118commits). Fullstep30 diagnostic/session85816
terminal0 confirms a DIFFERENT failure: owner7 eastrow277 has prescribed
INWARD3.1862347cm/s but particle movesOUTWARD. Actual hit96.47218cmaboveexactbed;
wet and no terrainpenetration.53other exitsapproved. See updated
[integration review](liquid-exact-exit-bed-integration.md) and
`liquid-native-exact-bed-exit-debug/exit-diagnosis-v2.json`.
Next trace/fix native physical inlet advection vs ghost-grid Dirichlet velocity;
do not loosen exit gate or silently delete water. All build/UE handles terminal,
no current process. No accepted sustained denseflow, scene promotion or commit.
The following entries are chronological prior evidence, not current status.

Latest: [exact exit bed integration](liquid-exact-exit-bed-integration.md).
Previous turn was progress (prepared exact bed curves). GPU ExitPlan/classifier
now accepts complete continuous bed knots; evaluates bed atactualfirsthit while
preserving original row stage/normal and invalid/firstface/dry/belowbed gates.
Dense loader validates parent frame/source SHA256. Build8812 failed syntax,
fixed build41259PASS. Engine-exact-exit-bed/session65117 terminal0:13pass,
1unrelatedHTTPwarning,0fail/RHI; paired GPU valid/real-belowbed case passes.
CPU optional pointwise reference +2tests;301PythonPASS.
Dense exact-bed-flow-v1/session92728 terminal1 BEFOREsimulation: generic Windows
SHA256 platform call unimplementedassert. Replaced with bundledOpenSSL SHA256;
do NOT remove provenancevalidation. Build6053 CURRENTLY LIVE (123actions full
editor-module rebuild for new dependency; most recent observed23/123). Resume
write_stdin6053; no other build/UE live. New LiquidFaceBedProfile engine test added
AFTERthis build began, so run incremental build after terminalsuccess to include
it. Then test newprofile+13regressions and run fresh120stepdense label. No accepted
denseflowyet with exactbed, no map changes/promotions/commit. Fullgoalactive.

Latest: [dense outlet pointwise bed](liquid-dense-outlet-bed-review.md).
Previous turn was progress (neighbor storage fix). This pass allows120dense
compact steps/118commits within8192record ceiling; optional one full dense audit
step only. Failed driver now preserves stages.json. Build95068PASS; dense-flow-v1
session7184terminal0 capture is REJECTED: firstGPUcontrol failurestep18 bit64.
16successful commits through17 retire1396particles, finalacceptedlive718539.
Later counts/exits are NOT committed flow. Full diagnostic build51159PASS,
session7867terminal0 (dense-exit-debug) firstfails15; retains18's fullpayload.
Independent example owner3/east/row224: hitZ593.0981684, exactmeshbed591.0981717
(2cm contactclearance), rowmidpointbed601.0784178. Exit wrongly uses midpointbed
for whole50cmrow. Do NOT weaken gate or flatten contact mesh.
New build_liquid_face_bed.py and4tests generate exact triangle/physical-face
intersections: tmp/south-fork-liquid-face-bed-20260910/physical_face_bed.json,
303/305/1273/1273knots, independentheightmaxerror1.954e-14m; no collapsedfloat32
intervals.299liquidPython testsPASS. No GPU integration yet; failure remains.
Next: validate/upload continuous bedprofile in ExitPlan, sample atactualfirsthit,
keep outgoing/stage/firstface/invalidsegment conditions, GPU+CPU slopingbedtests,
rerun120dense. Both builds/UE terminal; fulloriginalqueueactive, no promotion.

Latest: [dense native neighbor storage](liquid-native-dense-neighbors-review.md).
Previous user-status turn was no progress; resumed by inspecting actual captures
and code. Compact history (912 bytes/3 commits) now supports all719335 prepared
seeds and unchanged nominal47.006805m3/s parent forcing. Dense-v1 failed rawP2G
only inowner4. Native NQ buffer growth retained cached SRV/UAVs of old storage;
refresh all neighbor views after aligned Spawn/Update before complete insertion.
No engine source edits. First copy-based NQ diagnostics v1/v2 are REJECTED for
missing BUF_SourceCopy flags. Final snapshot is shader-read into owned storage.
Dense-nq-v3/session16324 terminal0: all719335original+149births=719484survivors,
3commits,5refreshes/steps,223groups; exact current owner4 neighbor membership85762
particles/22887cells. RawP2G passes all12owners unchanged,0reductionmismatch,
20072nonzero sharedcells. Owner4 mass1786.7081241vs1786.7083866expected.
Physical14973.3441127vs14989.2504467 with originalbound173.7878288m3, not sustained
mass/discharge acceptance.295Python tests pass; latest build86747 terminal success.
Engine-liquid-dense-neighbors/session79506 terminal0:13successes,0testwarnings/
failures/RHI errors. Includes signed shader snapshot without native copy flags.
Full retained liquid-native-neighbor-restart/session35034 terminal0, auditPASS:
both generations inPID19596 pass12initial+10births-3exits=19survivors, complete
payload/identity/exit history and original rawP2G.295Python tests still pass.
All owned builds/UE/auditor processes terminal; scoped whitespace check clean.
Saved reviewmap SHA unchanged. Next: extend dense
source/exit/allocation/repopulation, then actual surface/foam/raft/reference/FPS.
No map promotion or final commit. Original full queue stays active.

Latest: [native generation/restart](liquid-native-restart-review.md).
Previous goal turn was progress (actual inlet/outlet transport). This pass adds
WaterDetail Public/RaftSimLiquidLifetime.h, claimed generation/step tokens in
NativeParticleHandoff.Issue, metadata on samples/handoffs/stage groups and independent
generation/restart auditors. 285liquidPython tests pass. Actual same-process restart
found/fixed (1) transient system name reuse via MakeUniqueObjectName and (2) initial
multi-tick reset batch losing imported particles before incoming dispatch reserve.
Driver now observes first native tick before queuing more, and probe refuses
handoff until ReservationReady. Build13066 terminal succeeds. Restart-v3/session41397
terminal exit0; both generations inPID28708 pass full audits:12initial+10births−3exits
=19survivors,9commits,117movingsegments each. Original rawP2G/reduction passes both,
physical0.39583458469132893/0.39583434810811013 vs0.39583334513008595 expected;
numericbound~0.005132859061343158,zero reductionmismatches,76/84sharedcells.
Rejected v1/v2 retained; do not reuse them as successful restart evidence.
Engine13regressions including LiquidLifetime/session29021 terminal exit0:all13
success,0failures/RHI errors,one unrelated HTTP connectivity timeout warning.
All owned engine/build processes terminal. New lifetime observes first-stage
spawn plans and gates transfers; it cannot cancel already-dispatched engine births.
Next sustained/dense allocation/dispatch and empty-region repopulation, actual
prepared fluid + calibrated parent forcing, original single-surface/foam/raft/
reference/FPS and remaining river/crew/cleanup/release queue. No map promotion.

Latest: [live outlet and simultaneous source emission](liquid-native-outlet-review.md).
Previous status turn verified build23090 terminal success. This continuation
implements original-wet-seed outlet selection, first-step birth positions and
full independent survivor/exit/birth/segment auditor. Outlet-v1/session50315
terminal exit0 verifies12initial−3exits=9survivors,72moving segments and rawP2G.
Combined open-flow-v1/session79220 terminal but rejected: old diagnostic stops
commits at9 and capturesP2G11, leaving a moving uncommitted source-crossing gap.
Build44972 terminal success fixes retirement fixture to continuous commits until
the step immediately before P2G. Open-flow-v2/session13653 terminal exit0 verifies
12initial+9new−3exits=18survivors,9commits,109moving segments,owner7empty,owner0=17.
Final18particle rawP2G/reduction passes84sharedcells,0mismatches,physical
0.37500097911015473 versus0.3750000111758709m3 expected within original numerical
envelope0.004858227315396016. Final positions remain identical from immediately
preceding commit to pre-advection P2G; motion is proven between consecutive
commits, not invented in that no-advection interval.279liquidPython tests pass.
Engine12regression session29334 terminal exit0: all12success,0failures/RHI errors;
one unrelated Google connectivity HTTP timeout warning. All owned engine/build
processes terminal. No map change, promotion, visual/FPS acceptance.
Next reset/generation/identity lifetime and bounded repopulation/allocation, then
dense actual calibrated flow/single surface/foam/raft/reference/FPS and full queue.
The default closed-population auditor still refuses retirement; rawP2G explicitly
uses new full retirement auditor when that flag is enabled. All source/exit volumes
and birth sequence counts remain independently checked. Test source1 is prescribed,
not calibrated inletQ; outlet7 uses actual wetseeds with authored8m/s axial velocity.

Latest: [survivor/exit transaction](liquid-retirement-transaction-review.md).
Previous goal turn was progress (GPU exit classification). Optional exit evidence
now drives exact survivor/exit assembly. Evidence binds exact source snapshots
and positive native volumes; bit64 rejects any mismatched/rejected evidence.
Ledger copies every retired word/reference/crossing, source5counts(4faces,total),
source capacities and volumes. Legacy no-evidence exterior bit2 remains intact.
Native commit's same gate prevents ALL native writes on failure; all-exit tests
clear native live count/ID lookup and restore all free handles. Build99275 succeeds;
engine-retirement-v1/session72939 terminal exit0:12success,0warnings/failures/RHI.
Final build91837 terminal succeeds with NativeHandoff optional ExitPlan/StepStart/
Volumes integration and saved ledger fields in NativeAssemblySample.Adopt/Save.
Probe flag `RaftSimRegionalParticleRetirement` binds validated parent profile;
it does NOT change inner-corner fixture or enable parent forcing. Closed-population
auditor now refuses retirement captures until a dedicated full ledger auditor exists.
Live retirement-closed-regression-v1/session97577 capture/audits pass:18particles,
84moving segments,original rawP2G/conservation/reduction, no RHI errors. Session97577
subsequently terminal exit0; all owned engine/build processes terminal.
261liquidPython tests pass. Saved map unchanged. Goal active.
Next actual wet-seed outlet fixture + independent native survivor/exit ledger
audit and continuing motion/births after emptying, not a zero-exit acceptance.
Then lifetime/reset/generation, sustained dense fluid and original scene gates.

Latest: [physical parent exit classifier](liquid-exit-classification-review.md).
Previous turn was progress (native segment implementation/verification). Added
GPU segment/parent-face classifier and validated exterior-profile adapter. It
does NOT yet retire particles; assembly bit2 still rejects exterior sources.
New files: WaterDetail Public/Private `RaftSimLiquidParticleExitGPU.h/.cpp`, shader
`RaftSimLiquidParticleExit.usf`, engine test `RaftSimEditorLiquidExitTest.cpp`.
FProfile::ExitPlan validates exact parent frame/spacing/owner count before using
its original1304rows. Candidate status0inactive/1inside/2approved/4rejected/8invalid;
uint4 holds status/face/row/float32t bits. Counts8:inside,4approvedfaces,rejected,
invalid,sourceLive. Reads full native packet + step-start offset; no native writes.
Approved only first unambiguous horizontal box exit abovebed at wet normal<0row.
Floor/roof, dry/solid/inlet rows, outside/nonfinite starts and malformed routes
are not exits. Crossing row sampled at hit, not endpoint; spray above stage allowed.
Initial test C++ compile fixed; shader-v1 root parser crash fixed by separate
global declarations; v2 RHI input readback flag fixed with BUF_SourceCopy.
Final build17727 terminal succeeds. Engine-exits-v3/session33857 terminal exit0:
all11tests pass, no warnings/failures/RHI errors;261liquidPython tests pass.
All owned engine/build processes terminal. Saved map unchanged. No blocker.
Next atomic survivor+exit ledger integration and actual native outlet replay,
not merely relaxing assembly's exterior gate; then generation/reset/lifetime,
dense water/surface/foam and all original scene/reference/raft/FPS requirements.

Latest: [native pre-advection segments](liquid-native-segments-review.md).
Previous goal turn was progress (live emission/conservation verification). This
pass adds position-typed `RiverStepStartPosition` in the first post-spawn particle
stage before FLIP_PICforce, discovered native offset and exact segment auditor.
Build5599 succeeds; live-segments-v1/session11415 terminal exit0 proves84 moving
segments across7 consecutive step pairs with bitwise-correct starts,18 refreshed
origins at P2G. Existing birth/handoff and rawP2G/reduction audits still pass.
Engine-segments-v1/session53990 terminal but one test failed the too-literal
shader-string assertion; actual SetVariables indirection was inspected and the
test corrected to check both links, invocation and native loading. Rebuild70120
terminal succeeds. Final engine-segments-v2/session19238 terminal exit0: all ten
tests succeed, one unrelated Google connectivity HTTP timeout warning, zero
test failures or RHI errors. All owned engine/build processes terminal.
261liquidPython tests pass. Native ABI now14float/6int components with start
position offset3 in the observed capture; always discover offsets from metadata,
do not hard-code them. Full packet and handoff audits copy all20 words.
Next actual open-parent-face crossing classifier plus atomic exit ledger/retirement;
current exterior rejection remains unchanged. No visual/FPS acceptance or promotion.
Saved geographic map SHA256 remains36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96.

Latest: [continuous native emission](liquid-native-emission-review.md).
2026-09-10 verification continuation: preceding user status turn was no progress;
this turn completed live verification. v3 rejects the first-commit crossing gate
(zero changes at step2, later crossings/motion present). v4 uses the already
supported diagnostic speed8, with unchanged audits: nine initial plus nine births,
eight commits, nineteen owner changes, all18 retained, raw P2G/reduction pass.
Physical0.375001023347977 m3 versus0.3750000111758709 expected within original
bound0.004773083203743487. Emission-v4/session50601 terminal exit0.
Engine-liquid-emission-v1/session35642 terminal exit0: ten tests pass, no warnings,
failures or RHI errors;255liquidPython tests pass. Non-emitting seeded replay
liquid-native-neighbor-regression-v1/session45906 terminal exit0: twelve particles
survive three commits, changes[4,8,0], all twelve move on following step; rawP2G
passes step6,94 shared cells,zero reduction mismatches,clean RHI. All owned
Unreal processes are terminal. No new build since successful37985.
Next native pre-advection position and explicit open-parent-face exit ledger,
then reset/generation, lifetime/allocation and dense connected fluid. Current
exterior rejection stays fail-closed until real crossing/retirement is proven.
Implementation anchors: `RaftSimEditorLiquidTerrainContact.cpp` creates the first
post-spawn `Regional Neighbor Insertion` particle stage. Native advection/contact
is the later `FLIP_PICforce` stage. `RaftSimLiquidParticleIdentity.h` demonstrates
typed particle assignment through public Niagara graph APIs. Capture the true
position before advection into a persistent native attribute, not previous
owner-center/velocity extrapolation; account for full-word ABI offsets afterward.
`RaftSimLiquidNativeParticleHandoff.h` snapshots and commits actual native words.
`RaftSimLiquidParentExterior.h` validates the shared exterior profile; v3 boundary
rows contain bed/stage/inward-normal speed, followed by vector velocity rows.
Outflow must use this physical parent geometry and an atomic retirement ledger,
not silently skip the existing exterior error bit2 in assembly.
No scene/reference/FPS acceptance, map promotion, commit or external blocker.

Prior implementation checkpoint:
Previous turn was progress. Added bounded native source activation after initial
birth, actual per-step native spawn-plan fields and full emission/history audit.
v1 failed handle gates: native birth IDs896 require full1024IDtable despite129
particle capacity. Separated capacities and fixed snapshot/free-table audits.
v2 passes9initial+9new births,18particles/eightcommits/15ownerchanges, but FAILS
rawP2G by exactly one particle's volume. Root cause is spawn/update-relative NQ
slot collision. Moved NQ writer into one standalone post-spawn particle stage;
no engine changes. Added NiagaraCore dependency/public node construction after
an initial link failure. Final build37985 succeeded; 255liquidPython tests pass.
Native emission-v3 replay is live at checkpoint write; poll its owned handle
before more Unreal/build work. Audit it without relaxing gates, then engine
regression and exits/reset/lifetime/dense fluid/surface/original scene acceptance.
Saved map unchanged; no final commit/push, no external blocker, goal active.

Latest: [initially empty native receiver](liquid-empty-receiver-review.md).
Previous goal turn was progress. This pass fixes early-free suppression of manual
capacity on empty native owners and reserves their bounded dispatch upper count.
The early-free override is transient/scoped and restored during StopProbe.
Empty-receiver-v1/session50889 terminal: all nine particles imported into initially
empty owner0, survive three native commits, move on step6; exact payload, identity,
epochs/free tables and P2G pass, RHI clean. 249 liquid Python tests pass. General
handoff mode now includes this reservation too; build73985 succeeded. Fully seeded
reservation-regression-v1/session35618 exited0: all12particles retained and moving,
three commits with changes[6,3,0], exact state/identity/free/history and native P2G
pass, RHI clean. All owned engine/build processes terminal. Next continuous births/exits, reset/generation
and allocation budgets, then dense regional fluid/surface/foam and original
scene/raft/reference/FPS acceptance. Saved map unchanged; goal active, no blocker,
no final commit/push.

Latest: [actual native particle handoff](liquid-native-handoff-review.md).
The preceding user status turn only polled the terminal process; this continuation
verified its evidence and implemented repeated native commits. Single commit
step4-v1: 12 particles, 6 native owner changes, all 12 move afterward, raw P2G and
identity pass. Ten engine regressions pass without warnings/failures; 248 liquid
Python tests pass. Repeated-three v1 fails RHI validation at native end-of-batch
counter restoration; v2 removes errors but only completes five steps by capture.
Fixed state using engine exported query, and poll actual native readiness instead
of guessing from editor frames. Final build72803 succeeded. Repeat3-v3/session32430
terminal: three commits with owner changes [6,3,0]; all 12 survive and move on
step6, exact payload/ID/free-table/epoch/history checks pass, native P2G passes
with zero reduction mismatches and 84 nonzero shared cells. Clean RHI log.
Final engine-liquid-commit-v3/session72461 exited 0: ten tests succeed without
warnings/failures, RHI log clean. All owned engine/build processes terminal.
Next empty-owner allocation (engine early-free suppresses manual preallocation
on CPU-empty owners), births/exits/reset/lifetime, dense fluid/surface and original
scene acceptance. Saved map unchanged. Goal active, no external blocker; no final
commit/push.

Latest: [receiving persistent handles](liquid-particle-handles-review.md).
Previous goal turn was progress. Added GPU stable staying handles, collision-free
incoming local IDs/acquire tags, ID lookup and complete disjoint free-ID prefixes.
Native handles-step3-v1:6stayers preserved/6imports rekeyed in staging; all12particle
word planes, birth identities and raw P2G remain verified. Nine final engine tests
pass without warnings/failures;243Python tests pass. No native commit yet and
no sustained flow, visual or performance acceptance. Next ACTUALLY apply the
receiving state/count/ID lookup at a correctly ordered native final group, reserve
dispatch/allocation before preparation and verify changed ownership on subsequent
native steps. Then births/exits, empty receivers, generation/reset/namespace
lifetime, dense regional affine water and original scene/raft/reference/FPS work.
Saved map unchanged; no commit/push. All owned processes terminal:
build51197/engine8098/native31587. Goal active; no external blocker.

Latest: [receiving-side particle assembly](liquid-particle-assembly-review.md).
Previous goal turn was progress. Added GPU preflight/compaction/final accounting
for full-state receiving buffers. Native assembly-step3-v1:12particles assembled
exactly once,6cross-owner destinations; all float/int word planes bit-exact against
source. P2G/reduction/birth identity remain passing. Eight engine tests succeed
(one unrelated HTTP timeout warning);240Python tests pass. NOT native dataset
commit, subsequent-step handoff or dense flow, visual/performance acceptance.
Next apply receiving state with local ID/acquire-tag/free table and live-count
consistency, bounded native dispatch/spawn reservation, generation/reset and
sequence lifetime. Then dense regional affine transport, shared surface/foam,
raft and original geographic/reference/performance acceptance. Saved map and
prepared manifest unchanged; no commit/push. All processes terminal:
build89304/engine94062/native94047. Goal active; no external blocker.

Latest: [full-state native routing candidates](liquid-particle-routing-review.md).
The preceding status-only turn was no implementation progress; this continuation
fixed the pending build errors and verified the actual routing kernel. Seven
engine tests pass with no test warnings/failures;236Python tests pass. Native
routes-step3-v1 retains12particles across all12owners;6physically cross a region
boundary, with full-state staged destinations independently verified. Position,
velocity and integer identity snapshots match exactly; raw P2G/reduction still
pass,72nonzero shared cells. This is NOT native import/export or sustained wet
flow: particle ownership in Niagara is still unchanged. Next bounded destination
assembly/commit, native count/ID/free tables and dispatch/spawn budget integration,
generation/reset/sequence lifetime; then dense wet transport, surface/foam and
the full rapid/raft/reference/performance acceptance. Saved map/manifest hashes
unchanged. No visual acceptance or commit/push. All owned processes terminal:
final build39669/engine19822/native1584. Goal active; no external blocker.

Latest: [regional birth identity](liquid-particle-identity-review.md).
Previous goal turn was progress. Installed integer RiverBirthOwner/Sequence in
regional spawn; added exact int4 native GPU snapshot and same-run birth/later
identity audit. Native-identity-12-step3-v1:12distinct identities preserved,
native sequences0/1/2 across4owners;48nonzero shared cells; raw P2G matches
reference, exact reduction, physicalvolume0.25000078650191426m3. No actual
ownership changes/handoff yet. Six engine tests all succeed, one unrelated
HTTP connectivity timeout warning;232Python tests pass. Saved map unchanged,
no visual/performance or sustained-flow acceptance, no commit/push. Next actual
same-step native particle routing/import/export with all state/birth tags;
bounded dispatch/allocation, native ID/count/free tables, generation/reset and
sequence-wrap contract. Then regional affine state/connected wet conservation,
shared surface/foam and full-rapid original acceptance work. All handles terminal:
final build16655/native66597/engine64295. Goal active; no external blocker.

Latest: [native particle transfer](liquid-native-transfer-review.md).
The status-only turn made no implementation progress. This continuation tested
the pending spawn fix: actual four-owner packet v5 passes independent raw P2G
and exact conservative reduction. Later packet-step3-v2 also passes, all four
particles survive and move6.60–7.18cm worldX,24nonzero shared cells. Fixed
spawn-time NQ insertion (formerly no first-step deposits), inherited21m fixture
kill, and a late-snapshot diagnostic fence. Final engine-native-packet-v2:
5pass/0warn/0fail17.1888s;228Python tests pass. Zero-particle native transfer-v5
terrain1587600/shared143040/inlet898/outlet6720 checks remain exact. No saved map
change, no visual/performance or sustained flow acceptance, no commit/push.
Next actual global particle identity and bounded native count/ownership handoff;
then regional affine state, dense/connected wet tests, shared surface/foam and
full rapid/raft/reference/performance. Native persistent IDs/counts are local;
do not copy just positions or raise GPU counts beyond prebuilt dispatch bounds.
All handles terminal: final build39164/later packet81600/engine58682. Full goal
remains active; no external blocker. Map SHA36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96 unchanged.

Latest: [regional raw momentum/volume transfer](liquid-regional-transfer-review.md).
The previous status-only goal turn was no progress; revalidated queue/source and
implemented native raw P2G publication, GPU conservative owner/halo reduction and
native velocity/support resolve before Compute Boundary. Corrected actual runtime
DI ownership: user overrides had no named attributes; emitter-spawn defaults do.
All12 ZERO-PARTICLE native v4:1518aligned groups,30reductions,1160pressure and29
boundary exchanges. Terrain1587600/shared143040/inlet898/outlet6720 cells remain
verified. Engine v8:5pass,0warn,0fail,17.14s;224Python liquid tests pass. Still NOT
native wet transfer, realistic water or performance acceptance. Next nonempty
native P2G reference audit and same-step particle handoff, connected wet D/P/G,
shared surface/foam and full-rapid/raft/reference/performance. No scene change,
commit or push; full goal active. Final build91265/native94442/engine57068 terminal.

Latest: [parent-domain exterior forcing](liquid-parent-exterior-review.md).
Previous shared-boundary turn was progress. Installed validated parent face
tables, explicit canonical inlet query and parent-indexed outlet pressure while
preserving regional caps/shared ownership. First GPU velocity comparison exposed
half conversion mismatches; f32tof16 attempt did not resolve them; explicit
nearest-even lattice does. Final liquid-parent-exterior-v3 native ZERO-PARTICLE
run verifies898 exact inlet velocities,6720outlet pressures, no spurious internal
forcing/outlets. Shared143040cells and terrain1587600cells remain exact. Final
engine-liquid-parent-exterior-v3: four pass/no warnings/failures,13.622s;224Python
tests pass. No wet conservation, visual or performance acceptance, no map change
or commit/push. Next raw conservative P2G weight/momentum before normalization,
particle handoff, current velocity sync, connected wet tests and surface/foam.
Retained region-004-native.hlsl shows the native rasterizer currently normalizes
inside its neighbor query; copying normalized velocities is not conservation.
All handles terminal (build32507,native76433,engine86102); no UE/build process.
Full queue/goal active. Map36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96 unchanged.

Latest: [shared regional boundary exchange](liquid-regional-boundary-exchange-review.md).
Previous pressure phase/ownership turn was progress. Added typed RGBA16F native
boundary tuple exchange and installed it after complete Compute Boundary groups,
before downstream extrapolation/D/P/G. Actual all12 empty run:29 boundary and1160
pressure exchanges,1518aligned groups. All5960 shared columns/143040 cells match
physical-owner values exactly, all4half components. 1587600terrain cells and
2113056nonzero pressure-marker values remain exact. 219Python/three engine tests
pass without warnings/failures;16-owner GPU test includes all types/signed values
and two same-graph updates. No wet mass/particle transfer, exterior forcing or
visual/performance acceptance yet. Next explicit parent exterior forcing,
conservative P2G/particle handoff, wet projection, shared surface/foam/full rapid.
Build94097,engine5049,native64303 terminal; no UE/build process remains. Map SHA
36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96 unchanged.
No commit/push. Full goal/queue remain active, not complete.

Latest: [regional pressure ownership](liquid-regional-projection-review.md).
The preceding user-requested status answer made no implementation progress;
this goal continuation revalidated current state and implemented the next
pressure integration step. Regional compatible D/P/G now has the actual XYZ
metric, global reflected-Y phase, and shared halo write protection. Actual
native first-color nonzero marker readbacks match all2113056 cells exactly,
including shared/corner halos and partial X tails. All12 empty regions still
exchange pressure after every iteration;1587600 terrain masks remain exact.
215Python tests and three engine tests pass; no wet flow or visual/performance
acceptance. No saved map changed, no commit/push. Next exterior/shared boundary
masks/forcing, conservative grid/particle exchange, connected wet projection,
shared surface/foam and full-rapid validation. Full queue/goal remains active.
Final build59888 and test94619 terminal: engine-liquid-regional-projection-v2
three pass/no warnings or failures,7.790s. All probes terminal (40669/8661),
mapSHA36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96
unchanged. No live UE/build handle to resume.

Latest: [regional contact bindings](liquid-regional-contact-bindings-review.md).
Previous pressure-exchange turn was progress. Explicit canonical contact mode
removes legacy-window translation dependence. Shared primary terrain projection
installer, matching v3 regional page bindings, centered/grid-local P2G and exact
pressure terrain query installed on unused clones; regional Landscape fallback
removed so captured triangles are the sole terrain authority. All12 native empty
regions run:1587600 interior GPU classifications match source triangles exactly,
all5960 halo addresses match,1160pressure exchanges. 211Python/four actual-RHI
tests pass (one unrelated HTTP warning). Legacy wet refactor replay core audits
pass; viewed glossy/lumpy isolated volume still rejected,90.410s is not FPS.
No wet regional coupling, exterior/shared rules, particle transfer, visual/perf
acceptance or map promotion. Next global pressure phase and exterior/shared
rules,conservative P2G/particle transfer,shared surface/foam,wet/full-rapid checks.
All handles terminal:build45675,probe49515,test29408,wet37321. Map36f4bc42...unchanged.
No commit/push; full queue and goal remain active.

Latest: [regional pressure exchange](liquid-regional-pressure-exchange-review.md).
Corrected failed build, added post-group finalization hook and one-dispatch
physical-owner-to-halo R32F exchange. Final actual twelve-region empty probe
`liquid-regional-stage-groups-all-v2` passes:1414aligned groups,1080pressure
exchanges,5960columns,alladdresses independently match prepared geometry,zero
misalignment/errors. 16-owner two-iteration exact GPU values plus three regional/
history tests pass (`engine-liquid-pressure-halo-v3`,14.163s,one unrelated HTTP
warning);207 Python tests pass. No wet coupled regions, visual/perf acceptance,
map promotion or commit. Geographic map36f4bc42...unchanged. Next explicit
regional contact/boundaries,global wide-stencil pressure phase,conservative P2G/
particle ownership transfer,shared surface/foam,and wet/full-rapid validation.
Do not mistake this zero-water native schedule/exchange probe for those steps.
All owned build/test/probe handles from this turn are terminal, including final
build17044,test29628,and all-region native probe25256. No engine process to resume.

Latest: [owner-scoped reconstruction](liquid-reconstruction-owners-review.md).
Previous regional-geometry turn was progress. Live reconstruction now keys
render-graph clock/foam/step history by attachment generation; stable entries
prevent cross-owner aliasing and preserve same-graph intermediate history.
Removed hardcoded square grid/readback metrics in favor of explicit allocation
layout; rectangular foam half-extents and matching strict Python audit layout.
207 Python tests and four final actual-GPU tests pass, no warnings/failures
(`engine-liquid-reconstruction-owners-v2`,4.970s). Includes interleaved differently
sized active/paused/reset histories,17 foam cases and all12 regional geometry
mappings. The live console still attaches one fixture; this is not twelve active
coupled Niagara systems. Region frames/contact installation and conservative
iteration-level pressure/grid/particle/foam exchange remain next.
Legacy wet `liquid-reconstruction-owners-regression` passes core audits:759
callbacks714positive,45render-only,30distinctimages,57287primary56007supported;
maxP2.163714e-6m, affine3.779895e-6/s, noengineerrors. Existing SimCache warnings.
Viewed glossy/lumpy isolated patch remains visually rejected;86sblockingcapture
is not FPS. No actual regional/v3 contact, partial-X wet or performance acceptance.
All handles terminal:build95174/9676/11206,test97586/84171,wet57759; read-only
search9955 stopped. Map36f4bc42...unchanged. No promotion/commit; full goal active.

Latest: [regional geometry](liquid-regional-geometry-review.md).
Previous status-only turn was no implementation progress. Added all twelve
contact pages and exact exterior/shared/diagonal halo mappings, plus engine
boundary builder. Insufficient corner query support extended from original mesh
without deformation; float32 page-rebase parity failure fixed by anchored v3
contact ABI, not a looser tolerance. All 719335 seeds retain exact ORIGINAL-parent
contact results; all356320 extended triangles verified against source;
88044 computational centers/98304 independent support probes pass. Source audit
`liquid-regional-geometry-source-audit.json`; data
`tmp/south-fork-liquid-regional-geometry-v4-20260910` (manifest1ce01f36...).
203 Python tests and four actual-RHI editor tests pass; one unrelated connectivity
timeout warning in engine report, no failures. Legacy wet replay
`liquid-regional-contact-regression` passes core audits:757 callbacks714positive,
30 motion frames,57242primary, maxP1.849964e-6m, noengineerrors. Viewed glossy/lumpy
isolated block still visually rejected. Not actual regional/v3 contact runtime,
partial-X wet, shared projection or performance acceptance. No production change,
guard bypass or commit. Next install explicit frames/contact/boundaries in a
coordinated live solve with per-region histories, iteration-level shared pressure
and conservative particle/grid transfer, continuous surface/raft/reference/perf.
All handles terminal:preparation87296,build6420/46226,engine33990,wet4424,audit2120.
Saved geographic map remains36f4bc42... . Goal active, full queue incomplete.

Latest: [regional engine state](liquid-regional-engine-state-review.md).
Previous partition/tail turn was progress. Added strict canonical parent/region
decoders and positive-frame Niagara source/seed arrays on unused transient
systems. Extracted common initial reader; regional startup uses exact seed count
under native timing gate. Important correction: native tank burst grows with
grid dimensions; 163840 is retained seed-table limit, not fixed native burst.
Actual-RHI final `engine-liquid-regional-state-v3` passes five tests, no warnings
or failures (32.210 s), including all twelve region decodes, original seed-row
identity and three configured GPU examples plus fourteen old coupling variants.
197 Python tests pass. SHA256/full-row audit rerun in
`liquid-regional-engine-input-audit.json`, prepared bytes unchanged.
Actual `liquid-regional-reader-regression` legacy wet replay passes clock/stage/
live/affine/foam: 756 callbacks, 714 positive-clock steps, 30 distinct frames,
57266 primary, max position2.290761e-6 m, no engine errors. Viewed glossy/lumpy
block remains visually rejected. No actual regional birth, wet partial-X or
shared-interface runtime verification yet. No region activated, v3 guard bypass,
production promotion or commit. Next matching contact/boundaries and explicit
frame across all consumers, per-region histories, conserved shared exchange and
single visible surface/raft/reference/performance validation.
Sessions terminal: build37174 failed FFrame ambiguity, build75601 success,
test7082 failed test-side TArray self-insert (retained v1 log), build62241 success,
test5689 v2 success; build76350 + inspection47394 success; build50038 success;
final engine21865 success, wet24874 success. Saved map unchanged (36f4bc42...).

Latest: [regional state and pressure tail](liquid-regional-state-review.md).
The preceding status-only turn was no implementation progress. This pass fixes
actual compatible pressure tail ownership for even non-multiple-of-four X
counts without dropping cells or raising caps. Builds and four actual-RHI editor
tests pass. Prepared the complete 719,335 seeds / 6,144 inlet sites into twelve
regions with seventeen shared-interface records. Independent reassembly audit
verifies every identity and physical cell exactly once, unchanged canonical
positions/velocity/weights. Output `tmp/south-fork-liquid-regional-state-20260910`;
audit `liquid-regional-state-audit.json`. Max region seeds158248/render1723392;
total render16904448 including halos is not a performance acceptance.
197 Python tests pass. Actual legacy wet replay `liquid-pressure-tail-regression`
passes clock/stage/live/affine/foam; viewed glossy/lumpy exposed-edge block, no
realism acceptance. This 68-cell replay does not exercise the new partial-X GPU
branch; exhaustive CPU ownership and actual compiled shader support only.
Next strict engine regional state/frame consumer, bounded contact/boundary
matching, wet partial-X GPU verification and conserved shared exchange. No
internal-face emitters, initial-state resets, v3 guard bypass, scene promotion,
commit or completion. Build97796, editor24364, replay19020 terminal success.
Final build51339 and actual-RHI editor7015 also terminal success; final report
`engine-liquid-pressure-tail-final/index.json` has four passes, zero warnings
or failures (22.177 s), including compiled tail-marker assertions. No live
UE/build sessions remain. Saved geographic map SHA remains36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96.

Latest: [independent native XYZ allocation](liquid-independent-allocation-review.md).
Prior boundary turn was progress. Inspected actual native Independent mode;
implemented owned primary-grid XYZ overrides with dependent Other Grid bindings
preserved and unchanged caps/coloring guard. Integrated into coupled halo path,
replacing max-axis inference. Actual zero-inlet v3 check allocates five solver
grids 68x36x24, reconstruction/RT 136x72x48; actual material binds 3400x2700x800
cm and correct frame. This is not full-rapid or water-physics acceptance.
Actual coupled 12 s RHI replay passes clock/stage/live/affine/foam checks:
757 callbacks, 714 positive-clock steps, 30 distinct motion frames, no engine
errors; existing SimCache warning. Viewed surface remains glossy/lumpy.
190 Python and six final actual-RHI editor tests pass, including 14 coupling
variants; builds succeed. Saved geographic map unchanged. No assets promoted.
All sessions terminal: inspection 97926 explicitly stopped after completed
report/ignored quit; builds 13216,47858(failed),94922,98206,98945; allocation
88948(failed Python accessor),22175,91090; tests 88146/61290; wet replay79978.
Next bounded source/seed/frame consumers and conservative shared exchange,
then full-rapid single-surface raft/reference/performance verification. The v3
installer guard remains until matching state is wired. No commit or completion.

Latest: [regional boundary/pressure metric](liquid-boundary-layout-review.md).
Previous contact-reader turn was progress. Shared boundary helpers now handle
per-axis extents, counts, origin and variable side offsets. Compatible D/G and
pressure read the same profile metric; stage-grid positions no longer hard-code
the old square. Validated v3 decoder added, but fixed installer explicitly
rejects v3 until native XYZ allocation and source/seed coupling are implemented.
190 Python tests and four headless editor tests pass; builds succeed. First GPU
run failed on duplicate stage axes (retained); corrected v2 12-second RHI replay
passes clock, stage-order, live, affine and foam audits, no engine errors. Existing
SimCache warning remains. Viewed surface still glossy/lumpy, no visual acceptance.
No full rectangular GPU runtime claim. Broad secondary coupling fields remain
false; sampled terrain contact passes. Saved geographic map SHA unchanged.
Sessions 90204/5332 builds, 97585 tests, 3690 failed capture, 7713 corrected
capture, 57163 audits all terminal. Next explicit bounded XYZ allocation and
conserved regional state/exchange, then whole-rapid single-surface/raft validation.
No production promotion, commit, or goal completion.

Latest: [whole-rapid profiles and bounded contact reader](liquid-whole-rapid-profile-review.md).
The preceding user status response was no implementation progress; this
continuation verified the prepared profiles and changed the actual engine
contact reader, primary/pressure query and secondary swept query for v2 local-XY
tables. Source package: tmp/south-fork-whole-rapid-liquid-float-seeds-20260910;
719,335 seeds, 6,144 sources, contact max error 0.00712528 cm under 0.01 cm.
Dry native columns no longer initialize false water; float32 seed sites are
sampled consistently without moving captured terrain. New extraction helper
retains bounded source quad rectangles verbatim and rejects unsupported bounds.
202 Python tests pass; editor build succeeds; two NullRHI decoder/frame tests
pass cleanly. They are not GPU execution or visual acceptance. All sessions
terminal (build 84437, editor 5125). No maps/assets promoted, no commit.
Full grid remains too large for current density/volume limits, which are not
relaxed. Full v3 boundary/source/seed runtime consumers and conserved bounded
live integration remain next, followed by single-surface raft/motion/performance
validation. Full goal stays active; South Fork is incomplete.

Latest: [whole-rapid domain preparation](liquid-whole-rapid-domain-review.md).
The previous adapter pass was progress. This pass removes the square-only
preparation limit and adds exact native rectangular-face selection. New prepared
package: tmp/south-fork-whole-rapid-liquid-native-20260910, physical faces
(-112.5,-40.5) to (132.5,40.5), centre (10,0), size 245x81 m. All 4,226 recovered
rock vertices and all four rock-search polygons covered; coverage overlay viewed.
172,538 exact top triangles; max source error 5.82e-12 m. Actual native storage
derivative audit passes at 6.23e-7 m3/s error. The first interpolated package has
two dry-shore conflicts, retained; selected native-flux remap has zero conflicts,
Qin/Qout 47.006805/46.893871 numerical m3/s, no wet support invented. Source and
solid hashes preserved. 17 tests pass, processes terminal, no UE or map mutation.
Next generalize downstream source/initial/contact profiles and bounded runtime
layout for whole-rapid coupling; current 68x68x24 fixture cannot consume the new
package unchanged. Join to one continuous surface and shared raft/current state,
then actual-engine reference/motion/performance checks. No production or commit.

Latest: [geographic liquid registration](liquid-geographic-frame-review.md),
September 10. Rejected negative actor scale: it collapsed native Niagara volume
Y to 2. New opt-in source/query adapter keeps positive native grid dimensions,
reflects forcing and initial state, inverse-maps terrain queries, and handles
both primary and separate secondary swept contact. Captured source data and
saved maps unchanged. Actual v6 12 s RHI-validated run passes material frame,
68x68x24 grid, live reconstruction, clock, per-stage timing, quadratic transfer,
foam transport and sampled secondary contact checks. 30 distinct motion frames;
zero engine error lines, existing SimCache volume warning. Still glossy/lumpy,
no convincing roller or full-rapid integration. 102 primary particles outside
physical window at final capture; mass budget unaccepted. Geographic helper test
passes; legacy-frame test also passes cleanly. All build/engine/audit sessions
for this pass are terminal. Prior status-only user response
made no implementation progress; this continuation changes code and adds actual
GPU evidence. No goal completion, commit or production replacement.
Next integrate the registered fluid with the larger source-aligned playable
obstacle/turn domain and continuous surface, then reference/motion/performance
validation. Do not substitute additional tiny-patch material tuning for that task.

Latest: [fixed surface coverage review](fixed-surface-coverage-review.md).
Geographic review now owns a fixed 270 by 162 m carrier at 1.5 m spacing, not a
raft-following 240 by 96 m patch. Actual v3 guided traversal: 64.866 s, 2,428
coverage probes, zero missing probes, exact submitted hull-mask agreement,
607 wet samples, no ground penetration, max route error 4.923 m (narrow pass).
One existing render-thread CVar warning. Initial v1/v2 failed because they
incorrectly demanded water inside the raft; retained as evidence. New overhead
shows downstream rock groups continuously covered; water/rocks still not realistic.
Warm 720-frame overhead profile: 62.39 FPS, game/render/GPU 16.00/8.03/5.27 ms,
zero chart hitches, actual 1280x720 letterboxed view at 60% resolution quality.
Not a full-scene FPS acceptance. Map SHA 36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96;
recoverable pre-edit map under tmp/south-fork-geographic-before-fixed-surface.
Sources and original unreflected map unchanged; all processes terminal.
Next source-aligned hole/turn and physical crest/roller in this larger map,
not the unreflected isolated liquid patch. Full queue active, no commit.

Latest: [geographic orientation implementation and traversal](geographic-orientation-review.md).
Source ENU was mirrored by mapping north to Unreal +Y. Added explicit optional
world_y_sign=-1, preserving original source coordinates and solver fields;
forward/inverse positions, currents and normals now agree, with matching water
winding. Separate corrected map:
`/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable`.
Actual engine parity test v3 passes cleanly; 254 mirrored collision probes pass,
max 0.003866 cm. Corrected guided traversal passes with one render-thread CVar
warning: 64.898 s, -55.435 to 110.248 m, 604 wet samples, no missing/grounded
samples. Actual captures 003/005/009 viewed; still coarse rocks/smooth water.
Next: larger corrected map's fixed-rock/turn identity, downstream visible-water
coverage, and consistent physical crest/roller. Old liquid fixture transforms
have NOT been migrated to reflected world; do not mix them. Original map/source
arrays unchanged, no production replacement or commit. All engine/build sessions
for this pass are terminal. Full queue active.

Latest reference pass: [actual footage and geographic test coverage](troublemaker-reference-coverage-review.md).
Inspected the user's YouTube reference at 10/20/30/35/40/45/50/55 s and older
full-geometry engine crux/runout captures. A new source-hashed overlay proves
the 21 m liquid test includes zero recovered-rock vertices and nearly none of
the reviewed surrounding rock regions. It is not the full obstacle/turn rapid.
The older geographic plot and geometry use different origins (image centre
versus selected crux); resolved their offset without moving any terrain.
Three new frame/registration tests pass. Next use the larger matched registered
rock playable geometry for the source-aligned full rapid comparison, then
select connected/local liquid coverage. Do not continue treating isolated
patch refinements as full-rapid progress. No new scene writes or commit.

Latest September 9 continuation: [compatible particle transport](liquid-compatible-advection-review.md).
Exact derivative tests show the grid divergence check understates compressibility
of particle interpolation: tent interior RMS 0.895 /s versus quadratic 0.133 /s.
An opt-in compatible averaged-face cubic/quadratic midpoint path now has actual
GPU precontact replay parity (57,549 applied / 1,789 fallback), with all 714
dispatches accounted for. 180 numerical tests and 16 engine tests pass (one HTTP
timeout warning). Visuals still lack the returning roller; mean/p95 editor
25.586/27.657 ms with retained 93.023 ms spike. **Primary-only experiment:** foam
and secondary interpolants are unchanged, so do not promote this as consistent
flow. Keep the particle-only surface correction as the current baseline.
Next: verify named-rapid landmarks/actual captured geometry and the inferred
submerged control against river references, then native forcing and physical
crest/roller. If retaining compatible transport, unify all flow consumers before
acceptance. No manufactured tailwater/bed change, no production promotion or
commit. All owned engine/build/audit sessions are terminal; full queue active.

Latest September 9 continuation: [particle surface and grid shelves](liquid-particle-surface-review.md).
Quadratic APIC transfer passes actual GPU moment parity and the 16-test engine
suite but alone produces smooth grid-aligned shelves and does not establish a
returning roller. Same-state scalar analysis identifies the binary occupancy
floor as the shelf source: 9,079 columns raised over 10 cm, 7,687 crossings on
solver-cell faces. `-RaftSimLiquidParticleSurfaceOnly` bypasses that floor while
retaining its audit control and live foam/boundary coupling. Actual 12 s capture
has only four rendered face crossings versus 7,735 in its unused floor; all 714
GPU steps, live/foam checks and sampled secondary contact pass. Spray inside
water is 0 / 24,962. Rounded/rippled shape and internal pockets remain, not
photorealism. Uninterrupted editor mean/p95 25.125/27.247 ms, reconstruction GPU
5.164 ms; not full-scene performance. Next: particle distribution/volume and
source/outlet/bed consistency, physical crest/returning roller, playable
integration. Do not reinstate categorical fill to conceal surface defects.
Use the new flag with quadratic transfer, continuous sparse kernels and muted
green optics for continued review. No production promotion or commit; full
queue remains active. All owned engine/build/audit processes are terminal.

Latest September 9 continuation: [continuous sparse kernels](liquid-continuous-kernel-review.md).
Fixed a demonstrated hard shape switch at 25 neighboring particles, behind
`-RaftSimLiquidSmoothSparse`. A weighted 8–24 transition preserves primary
positions/quadrature weights and passes actual GPU threshold-crossing tests.
It affects only 383 / 51,871 particles in the analyzed capture; dense-surface
lumps and regular ripples remain. A 12 s RHI-validated motion capture passes
all 714 dispatch/clock steps, live/foam checks and sampled secondary contact.
Final spray inside water is 0 / 13,046. 165 numerical and 16 engine tests pass
without test warnings/failures. Benchmark mean/p95 26.189/28.580 ms, maximum
33.625 ms; reconstruction GPU 5.464 ms, not a speedup or full-scene acceptance.
Ray-sampling checks did not establish missed intersections as the broad-lump
cause; grazing outliers remain and no raymarch change was made. Next: dense
free-surface geometry and source/outlet/roller physics, then playable integration.
Use the new flag with `-RaftSimLiquidTerrainRiverOpticsMotion` for continued
candidate review. All owned engine/build/audit processes are terminal. No saved
production promotion or commit; full queue remains active.

Latest September 9 continuation: [river optical comparison](liquid-river-optics-review.md).
Finished the per-step 60 s verification and benchmark described below. Added
explicit transient RGB extinction controls and tested nine fixed-state optical
cases: all captured simulation state is identical, material coefficients match,
and RHI validation is clean. Selected muted-green absorption/scattering with
roughness 0.22; coefficients are authored, not measured turbidity. A separate
12 s motion capture verifies all 714 GPU steps, live fields and active/paused
foam transport, with 30 distinct frames. 160 numerical tests and all 15 latest
engine liquid tests pass without test warnings/failures. The cyan cast is reduced,
but rounded fragments, regular ripples, coarse crests and rectangular fixture
faces remain visibly unrealistic. Next work is primary free-surface/fragment
geometry and physical roller/source/outlet consistency, then continuous playable
integration. Use `-RaftSimLiquidTerrainRiverOpticsMotion` for the selected review
profile; old controls remain available. No saved production promotion or commit.

Latest September 9 continuation: [current-surface stage review](liquid-current-stage-review.md).
Reconstruction now precedes secondary stages on every simulation substep, with
graph-local clock/foam history. Final RHI-validated runs verify 3,594 / 3,594
updates at 60 s and 1,428 / 1,428 at two substeps over 12 s (up to four steps in
one graph). Final sampled spray inside rendered water: 0 / 11,942; foam absolute
interface distance p95 0.952 cm. Live/affine/foam/contact sample audits pass.
157 numerical and 15 engine regressions pass; the engine suite predates the final
per-step edit, which is covered by the two actual RHI-validated captures.
The new uninterrupted benchmark is 26.038 ms mean / 28.732 ms p95, with a retained
101.764 ms spike; reconstruction GPU mean 5.410 ms. Not whole-scene acceptance.
Current visuals remain cyan/glossy with rounded fragments and rectangular review
edges. Next: controlled extinction/roughness comparison, physical crest/roller,
continuous playable integration and whole-scene performance. No saved asset
promotion or commit. Full queue remains active.

Latest September 9 continuation: [secondary exact-contact / endpoint review](liquid-secondary-exact-endpoint-review.md).
The isolated candidate now has swept registered-triangle contact and explicit
physical-domain bounds for secondary particles. End-of-step phase prediction uses
the previous completed surface with RK2 transport. At 12/60 s, all sampled
secondary particles are finite, exactly probed, clear of the bed and inside the
physical domain. The 60 s run verifies 3,630 live updates and stable foam transport;
**surface coupling still fails** (1,290 / 10,544 spray particles inside rendered
water). It remains glossy/cyan with rounded fragments and rectangular review
edges, not photorealistic. Editor mean/p95 is 26.42/28.34 ms, about 0.49 ms slower
than the earlier affine candidate. 149 numerical tests and 14 engine tests pass
(one HTTP connectivity warning); the first failed test report is retained and its
old-window source assertion is replaced by exact selected-profile plus saved-source
immutability checks. Next investigate explicitly ordered current reconstruction
before secondary updates; do not treat endpoint prediction as exact coupling.
Saved production assets unchanged, no commit, full queue active. All owned
Unreal/build/audit sessions are terminal at this checkpoint.

Latest September 9 continuation: [affine transfer and froth transport](liquid-affine-transfer-review.md).
The isolated liquid candidate now preserves local velocity gradients through
P2G/G2P. Actual GPU checks caught and fixed editing the wrong pinned Niagara
script version; the installer and capture now verify the executing path. Exact
sampling-coordinate and gradient replay pass at 12/60 s. Stronger breaking flow
exposed half-texture transport error; float32 RK2/history interpolation fixes it
without increasing the foam gain or audit tolerance. At 60 s, primary particles
are finite and clear of the exact bed, with measurable reverse/rising pool flow
and visible splashing/froth. Appearance remains too cyan/glossy and the required
roller has not been physically calibrated. Secondary contact/surface coupling
fails (73 bed penetrations, 1,354 spray particles inside rendered water).
136 numerical tests and 14 engine liquid tests pass. Editor benchmark mean/p95
is 25.93/27.90 ms, about 2.49 ms slower than baseline; not full-scene acceptance.
Next repair secondary exact-bed/current-surface coupling, then physical crest,
optics, single-surface playable integration and performance. Full queue remains
active, saved production assets unchanged, no commit. All owned processes are
terminal at this checkpoint.

Latest September 9 continuation: [control-centred liquid review](liquid-control-centered-review.md).
The old 21 m window excluded the hypothesized plunge-pool centre. A verified
coordinate-only rebase now includes both shelf and pool, preserving all captured
elevations, topology and hydraulic array bytes. New collision/profile review
assets are separate; the registered map and saved contact system are unchanged.
The first correctly attributed new capture failed foam-source parity. Explicit
float interpolation of exact half texels fixes that failure without changing
source thresholds or the auditor's tolerance. Actual 12 s and 60 s captures now
pass source/coverage/pause checks. Fourteen engine regressions pass (one unrelated
HTTP connectivity warning). A new non-affine GPU source test covers precision.
The final numerical suite passes 121 tests, including duration-aware audits
and longitudinal surface sampling. Saved system/map/project hashes match.
The uninterrupted editor benchmark is 23.44 ms mean / 25.53 ms p95, reconstruction
6.226 ms GPU, foam/copy/cache 0.163 ms; still not performance acceptance.
The 60 s water remains glossy and weakly frothy. Its selected longitudinal
surface strip has no returning upstream roller, despite a visible drop. Next
inspect interior drop/pool circulation and pressure/stage coupling; do not
increase whitening gain as a substitute. Secondary contact also fails. All
owned Unreal/build processes are terminal. No production promotion or commit;
South Fork and the full queue remain incomplete.

Latest September 9 continuation: [surface-source and breaking-flow review](liquid-surface-strain-source-review.md).
Surface foam now uses true tangential compression and excludes rigid rotation
without strain. 112 numerical tests and 14 engine tests pass; actual 12-second
coverage parity and exact pause stability pass. The image still fails realism,
and mean sampled-top coverage falls to 0.002389 after false sources are removed.
Uninterrupted editor mean is 23.04 ms, foam/copy GPU cost 0.142 ms; not performance
acceptance. An offline convex/outward crest diagnostic finds only 0.525% active
interior top columns. Median candidate depth is 1.87 m and surface speed 1.40 m/s;
these are not measured river depth or depth-averaged Froude. Next inspect the
primary drop/pool, imposed stage and inferred bed before adding more source
strength. Fixture origin is in the existing candidate constriction, but the
21m domain does not span the whole rapid. No primary geometry/physics or saved
production assets were changed. All processes terminal; full queue still active.

Latest September 9 continuation: see [shared secondary surface review](liquid-secondary-shared-surface-review.md).
Actual GPU source/classification now uses a timestamped copy of the completed
rendered surface, consumed next step. The final capture reduces spray inside
rendered water from 12/20 to 1/62; p95 absolute foam-interface distance is
0.954 cm. Cache equality, GPU consumption timestamps and paused state are
verified. 105 numerical tests and 14 engine regressions pass. The image still
fails realism: weak froth/glossy cyan water and rectangular fixture edges.
The paired editor benchmark is 23.38 ms control versus 23.52 ms with shared
surface support; extra GPU copy time is about 0.022 ms. Overall performance
still misses the frame budget. Next is realistic surface aeration and
persistence. No production promotion or full-scene acceptance.
This latest note supersedes older next-step instructions about correcting curl
or zero/one-particle emission, without converting earlier diagnostics to acceptance.

- Extended the half-metre hydraulic stability test by 120 simulated seconds from the last sane 90-second state. All 13 saved frames pass numerical sanity. The independent face-flux audit agrees with the storage derivative within 0.000005 m³/s. [Full result](extended_stability.json).
- Connected explicitly tagged captured static-mesh ground to the raft physics bridge. This closes the mismatch where visual/collision triangles were detailed but custom raft contact only sampled Landscapes or a coarser solver bed. Other scenery remains excluded.
- Registered the existing review terrain; no production map or hydraulic fields were replaced.
- Fixed a null review-game-mode pawn caused by an incorrect script module path. The actual gameplay guide now possesses and attaches to the raft; the generator fails explicitly if that class is missing.
- Added and ran a real-engine regression: four captured rock sites plus one bank, four headings each, 2,400 substeps, checked against independent world collision traces. **20/20 contact cases pass**, with no sampled tube penetration beyond the 0.1 cm tolerance. The same test verifies guide possession and attachment.
- Unreal build passed. Final engine run: **2/2 passed**, including registered water replay. Survey-sanity and scene-layout Python tests: **12/12 passed**.
- The clean camera-corrected 1280×720 offscreen run measured 21.616 ms mean / 28.168 ms p95 across 926 frames, with a 13.096 ms mean solver step. It fails the 60 FPS and solver-time budgets. These are engineering timings, not release qualification.
- Fixed performance-report GPU identification: the OS's primary display-device string said AMD integrated graphics, while the engine log identifies the actual rendering adapter as an NVIDIA RTX 3060 Laptop GPU. Future reports use the active RHI name and retain the platform-primary string separately. Historical reports were not overwritten.
- Repeated the clean benchmark after that metadata correction: **21.752 ms mean / 28.336 ms p95**, 920 frames, 12.905 ms mean solver step. `survey_performance_final.json` correctly names the NVIDIA adapter and retains **passed: false**.

The first collision test correctly failed: component traces do not guarantee the world-query `bBlockingHit` flag. The corrected implementation uses the component intersection result, and the test independently uses blocking world traces. Failed reports remain under `engine-tests`; passing final reports are under `engine-tests-final`.

## Not accepted

The fine-grid mean-flow screen still fails: tail storage rates exceed 2% of inflow, although the final-state flux audit is conservative. Spatial convergence and extended-duration stability remain unverified. The half-metre result stays out of engine fields.

Contact tests are controlled penetration/impact regressions, **not** natural whole-rapid traversal, D4 wrap/pin acceptance, or proof of every submerged obstacle. The production route is still the old roughly 49 km geometry. None of the 20 rapid search windows has received final identity/layout acceptance.

The first live screenshot burst was rejected: its camera was underneath terrain because the pawn class was null. Its performance report (`survey_performance_captured_ground.json`) includes screenshot overhead and the wrong camera and is not comparable to a clean boat-height benchmark. The follow-up clean benchmark is `survey_performance_guide_fixed.json`; it is an offscreen engineering diagnostic, not packaged-build qualification.

After the pawn repair, three live captures at 6, 9 and 12 seconds show the view
properly riding behind the crew and changing position with unpowered drift.
They are `unreal/Saved/Screenshots/SurveyGuideFixed20260907_000.png` through
`_002.png`. Visual acceptance still fails: the diagnostic terrain is plain,
the exposed channel edges look sharply cut, and the water lacks realistic
breaking relief and froth. No photographic likeness is claimed. The `-game`
capture log also contains an engine Python startup error about the unavailable
`PythonTestRunner` class; the process still produced all three captures and
exited normally. This is retained in the log rather than hidden.

## Recovery and next work

The review map's pre-registration backup is `tmp/project-cleanup/SouthForkSurveyPlayable-before-ground-tag.umap`. The review game mode's pre-camera-fix backup is `tmp/project-cleanup/BP_SurveyReviewGameMode-before-guide-fix.uasset`. Only restore exact files after checking for later changes. No commits or pushes were made.

Next: validate natural whole-rapid collision/animation traversal, resolve fine-grid storage oscillation and runtime performance, verify rapid landmarks against captured imagery, then migrate the route, terrain, collision, water fields and scenario starts together. Keep captured/inferred geometry distinguished. The current builds, finite-run check, guide registration and controlled ground-contact tests are completed; do not repeat the unchanged diagnostics instead of advancing these remaining steps. See the [South Fork plan](../plans/south-fork-evidence-reconstruction.md) and [reference cross-check](reference-review.md).

## Hourly continuation — solver face reuse

The next pass targets runtime work without changing resolution, CFL, waves,
boundary conditions or geometry. MUSCL stepping now reuses each interior
interface flux pair within one immutable integration stage. Both hydrostatic
bed-correction sides are retained; dry-cell skips explicitly invalidate cache
entries. The cache is only one row wide and is recreated for every RK stage.

Three alternating 100-step survey A/B pairs have bit-for-bit identical saved
frames. Median native wall time including exports is 9.636 s before / 9.133 s
after, a modest 5.2% reduction. All three native fixtures, the native survey
fixture and 12 Python survey/layout tests pass. See
[comparison evidence](face-cache-comparison/README.md). These are optimization
checks, not hydraulic settling, spatial convergence or visual acceptance.

This pass also found that UBT's archive `ExternalDependencies` invalidation did
not actually relink the old water DLL. A content-hash public compile definition
now forces consumers to rebuild when the externally built solver changes. The
generated compile hash matches archive SHA-256
`4a176cb3b37e358f435887ea4834436729eaeb6e3e8dcb71b43201c6f37d2b39`.
No scene or cooked hydraulic field has changed in this pass.

The editor rebuild completed successfully (154 actions, 920 seconds). The
clean, same-map 1280x720 offscreen benchmark after relinking recorded 1,012
frames: **19.783 ms mean / 27.209 ms p95**, with **11.057 ms** mean solver step.
The previous run was 21.752 / 28.336 ms, with 12.905 ms solver time. This is
roughly 51 versus 46 FPS by reciprocal mean, but still fails both frame and
solver budgets. It is one engineering run per build, not a statistical release
qualification; the native alternating trials isolate the face-reuse change.
See `survey_performance_face_cache.json` and `face-cache-build.log`.

Both rebuilt-engine regressions pass: `SouthForkCapturedGroundContact` and
`SouthForkRegisteredReplay` (`engine-tests-face-cache/index.json`). The existing
render-thread console-variable warning remains recorded; there are no failed
tests. All owned cook/editor/build processes have exited. No commits or pushes
were made. The next pass should advance natural traversal or unresolved
hydraulic/geometry validation, not repeat the completed A/B and build checks.

## Completion request — actual traversal and enclosed rock gaps

The normal-clock free-drift diagnostic is now implemented, built and run. It
travels about 146 m in 120 seconds, remains wet and finite, and has no missed
ground queries or meaningful sampled tube penetration. It then lodges against
a downstream rock and does **not** reach the outlet. The automation result is
retained as a failure, not renamed a successful whole-rapid traversal. Guided
traversal is still needed; contact must not be weakened to force an unsteered
raft through an obstacle. See [natural drift](natural-drift-review.md).

A separate captured-rock repair fills 40 enclosed half-metre cells (10 m²),
preserving all measured rock/bank values and open channels. The repair uses
authority code 4 for inferred interpolation, never captured bathymetry. Its
1-m cold cook (200 s) was conservative but still draining. A 400-s continuation
now passes the mean-flow screen: tail section error 2.41%, small storage change,
and regional stage change below 1 cm. All 14 saved continuation frames pass
sanity; maximum saved depth 2.865 m, speed 10.555 m/s. Numerical face flux and
storage derivative agree within 0.000003 m³/s. The instantaneous outflow is
still 2.6% above inflow; mean-flow screening is not strict instantaneous steady
state or spatial convergence. See [bounded evidence](rock-gap-candidate.json).

The candidate runtime fields are exported separately. The exporter now checks
the **actual geometry bytes**, not just a manifest's claimed hash, and supports
an explicitly selected diagnostic variant. Twenty-two repair, geographic and
export-identity tests pass. **The new mesh/fields are not loaded in the engine**;
they must be imported together before any comparison. Existing live review
geometry is unchanged. No production route or later river was promoted.

Primary South Fork hydraulic-jump research provides useful qualitative and
probe-air-content comparisons, but the identified sites are not Troublemaker.
No other rapid's measurements or geometry were silently transferred. See the
[reference follow-up](hydraulic-reference-followup.md).

### Single-carrier lighting comparison

The review map now selects a duplicated, surface-lit version of the former
volumetric overlay material. This fixes the nearly black approach water, as
confirmed in actual same-camera gameplay captures, but downstream water still
looks much too smooth. It is a review-only experiment, not accepted whitewater.
The shared material, production maps, geometry and physics remain unchanged.
The pre-change review map is backed up; the normal generator does not yet select
the experiment. See [visual and performance findings](surface-lighting-review.md).

Clean performance is 19.446 ms mean / 26.381 ms p95 across 1,029 frames, solver
10.835 ms: comparable to the preceding run but still over both budgets. No
statistical speedup or release qualification is claimed. Next work remains
coordinated candidate mesh/field import, guided traversal, physically grounded
breaking relief/froth, grid convergence and full-route migration. Do not repeat
the already completed initial cook, free-drift test or lighting comparison as
a substitute for those tasks. The queue is still not complete.

Final experiment regression run: both `SouthForkCapturedGroundContact` and
`SouthForkRegisteredReplay` pass (`engine-tests-surface-lit/index.json`). The
separate natural free-drift outlet test remains failed. Six edited Python
scripts parse, and the 22 repair/geography/export tests pass. Owned cook and
editor processes have exited; no commit or push was made in this pass.

## Hourly continuation — matching candidate loaded

The previously export-only gap candidate is now imported into the **same isolated
review map**, with its matching full-triangle collision, hydraulic package,
coordinate map and upstream start. The prior mesh and exact prior review map
are preserved. Production maps and shared materials are unchanged. This entry
supersedes the earlier "not loaded in engine" status; the old captures and
failed natural-drift result still belong to the old fixture.

All 16 imported collision-height probes pass, including four inferred gap cells;
maximum source-to-engine error is 0.001701 cm. The new candidate-specific native
replay test and the actual-scene captured-ground contact test both pass (2/2,
one preexisting console-variable warning). The old registered-replay test uses
the old fixture and was deliberately not counted as candidate validation.
Build passed; 21 Python layout/sanity/gap/export regressions pass.

Three actual gameplay captures confirm downstream motion with the new package,
but still show excessively smooth water and coarse rock/bank shapes. Clean
performance is 19.024 ms mean / 25.501 ms p95 over 1,052 frames, still a failed
frame-budget result. No full-traversal, convergence or visual acceptance is
claimed. See [integration evidence and recovery](gap-integration-review.md).

Next: physically grounded breaking relief/froth and guided natural traversal on
this now-consistent fixture, plus resolution convergence and runtime budget.
The standard old review generator still points at the old package; do not run
it blindly over this staged candidate. No new cook is required merely to repeat
this import. All owned processes have exited; no commits/pushes in this pass.

## Completion request — guided traversal and breaking ownership

The integrated candidate now has a normal-paddle guided traversal test and a
current-aware, footprint-clearance route planner. The planner does not change
geometry or claim measured underwater depth. Existing crew commands and guide
strokes carry the raft; collision, forces and solver fields are unchanged.
Ten route/ledger tests and nine subtests pass. An early outlet-only engine
success is explicitly rejected in the ledger because it wandered 39 m from
the route; all failed controller iterations are preserved.

The final baseline controller records one bounded pass at 81.13 seconds with
4.97 m maximum route error. An opt-in shared-breaking variant now records a
fresh-map pass at **80.11 seconds / 4.62 m maximum route error**, with no missed
ground queries or sampled ground contact. The corrected combined engine run
passes **3/3**: guided traversal, captured-ground contact and candidate replay.
Traversal tests now force a fresh map load so earlier tests cannot leave the
raft already drifting downstream. These are not robustness or full-route passes.

The captured review was still using the legacy overlay's 15 m breaking-site
exclusion, rejecting most local hydraulic transitions. The experiment
`-RaftSimSurveyBreakingReview`, restricted to this exact map and field package,
uses existing bounded shared render/support relief and local envelopes, with
the single-carrier wet-margin rules and no separate lip/roller water sheets.
Runtime assertions confirm one visible carrier, the coupled scale and up to
ten persistent breaking sites. Omit the flag for the unchanged baseline.

Actual same-camera 6/9/12-second comparisons show the detached upright foam
sheet replaced by carrier relief, but the ridge is too angular and foam still
looks bright and streaked. **Visual acceptance remains failed.** Clean
performance is **21.423 ms mean / 28.024 ms p95**, versus the earlier baseline
19.024 / 25.501 ms; both fail budget. No default or production rollout, map
save, new cook, commit or push was made. See
[full evidence and next work](guided-traversal-review.md) and
[the retained run ledger](guided-review.json).

Next: improve the opt-in crest silhouette/foam shading and CPU cost, establish
repeatable guided tracking, then continue rapid identity/layout verification,
resolution convergence and coordinated full-reach migration. Do not restart
completed import/cook/ground-contact work as a substitute. Colorado, Pacuare
and Futaleufu remain queued; the overall objective is not complete.

## Hourly continuation — hidden second foam response

Live mesh inspection found that the supposed single-carrier review still drew
`RapidFoamMesh` above its main surface. The earlier assertion excluded only the
volume core, lip and roller. Its historical passes are not proof of one foam
response. The scoped shared surface-lit path now hides that extra foam sheet
and skips its redundant mesh uploads; the guided assertion now includes it.

An actual fixed-camera bisect shows this removes the dominant hard bright
streaks. Removing emissive glow alone barely changed them. Existing main-carrier
foam parameters now provide softer aerated shading, opt-in through
`-RaftSimSurveyLitFoamReview` together with `-RaftSimSurveyBreakingReview`.
No material asset, map, geometry, collision, solver field or raft force changed.

Build passed. Final suite is **2/3**, with collision and replay passing. Guided
traversal reaches the outlet in 89.60 s without sampled ground contact, but its
5.846 m tracking error still fails the 5 m criterion. Its strengthened single
water/foam carrier assertion and all seven material parameter checks pass.
The raw failure is retained; there was no repeat-to-pass run or relaxed limit.

Clean frame time is **20.933 ms mean / 26.991 ms p95**, 956 frames. This remains
over budget; the small reduction from the previous 21.423 / 28.024 ms run is not
a statistically proven speedup. Actual captures still show angular crests and
inadequate foam surface detail, so visual acceptance remains failed. See
[findings, images, and next work](single-foam-carrier-review.md). All owned
editor/build runs have exited. No new cook, asset save, commit or push was made.
Continue with crest shape/detail, runtime cost and robust guided tracking; do
not rerun the unchanged failed controller or completed cook/import as progress.

## Controlled half-metre check on the integrated gap geometry

Refinement now inherits the parent's exact boundary forcing and rejects changed
solver, CFL, timestep, roughness, discharge or mode. Previously it recomputed
boundary stages at finer cell centres. Nineteen regressions and 22 subtests pass,
including nested area restriction and dry-edge exclusion.

A new 120-second fine-grid run uses the same repaired source geometry as the
current engine candidate, not the older geometry used by past half-metre runs.
Its 13 saved frames are sane (max depth 2.6993 m, speed 11.9751 m/s), and actual
numerical face flux matches the storage derivative with zero side leakage.
However, mean-flow settling **fails**: tail section error 6.29%, storage up to
4.499 m³/s. Crux final stage is 22.5 cm lower in the median than the coarse
parent, with 29.3 cm p95 absolute stage difference and 0.986 m/s p95 current
vector difference. The unsettled histories preclude claiming grid convergence.

See [experiment, evidence and next checks](gap-resolution-review.md). No engine
package was exported or imported; map/material/terrain/collision remain intact.
All owned processes exited, no commit/push. Investigate regional settling and
boundary/storage oscillation before any fine-grid promotion. Do not repeat the
completed warm start or old diagnostic. Later rivers remain queued.

## Regional settling and controlled continuation

The latest fine-grid tail's storage adjustment was concentrated downstream,
not at the crux. A new unchanged-forcing continuation advances the saved fine
state from 120 to 240 seconds since refinement. It does not reinitialize from
the coarse grid or recompute stages. The new restart guard verifies bed/grid,
geometry, axes, solver, timestep/CFL/roughness/discharge and constant boundaries;
cook outputs now refuse existing directories. Twenty-six tests and 32 subtests
pass, including physical area partitions and temporal-envelope diagnostics.

All 13 continuation frames are sane and actual face-flux conservation passes.
Section error improves to 4.69% (passes), but one tail storage rate is 1.445
m³/s (fails the 0.906 limit). Downstream fluctuations decay while the crux
median fine/coarse stage difference persists at -22.98 cm. 79.61% of common
crux cells have separated sampled stage envelopes (fine lower by >1 cm).
Sparse, unequal-duration tails do not establish formal spatial convergence.

The largest local fluctuation lies in a deep, slow pocket at grid (130,235),
downstream/left (-17.75,-15.25) m. Its source footprint is mostly inferred
submerged bed beside captured rock, not a previously repaired authority-4 gap.
Do not fix this by changing measured heights without evidence or conclude that
one pocket explains the whole crux bias. See [localized findings and handoff](gap-settling-continuation-review.md).

New USGS daily context for the 2022-07-21 atlas date is 584 cfs upstream; it is
not an instantaneous photo-time discharge or rapid stage. The diagnostic's
1600 cfs forcing is unchanged. No new engine import, asset change, cook field
promotion, commit or push. All owned work exited; later rivers remain queued.
Next: source/flux investigation of localized pocket interfaces and the broad
crux resolution bias, not another identical extension seeking a green tail.

## Off-vertex terrain mismatch corrected in the cook pipeline

Source review did not justify filling the open pocket or turning water-class
LiDAR returns into rock. It exposed a separate reproducible mismatch: terrain
render/collision uses source triangles while the cook used bilinear heights.
Identical source hashes and the previous vertex-only probes missed this.

The new sampler and shared triangle-index generator match actual engine
collision at 16 off-vertex points, max error 0.000265 cm versus 104.303 cm for
bilinear heights at those probes. The broader grid comparison reaches 1.328 m.
The first trace attempt lacked completed asset compilation; its failure log
is retained. The corrected read-only audit passes and leaves the map unchanged.

Fresh cooks now use `render_triangles`; continuations/refinements inherit and
verify their parent's interpolation. Old registrations remain explicitly
bilinear, raw resumes require an explicit method, and resolution comparisons
reject mixing methods. Export manifests record and validate the method. Tests:
33 plus 39 subtests, and 11 export/sanity regressions, all pass.

A separate 600-second 1-metre triangle cook is finite and conservative. Discharge
and storage screens pass, but crux median stage range is 10.612 mm, failing the
10 mm screen. No repeat-to-pass continuation was run. The corrected review
package is exported separately, **not loaded into the engine**; old loaded
fields, mesh, collision, material and map remain unchanged. No C++ build,
asset save, commit or push. See [evidence and guarded next steps](triangle-sampling-review.md).

Next: candidate-specific staged field validation and/or a controlled fine-grid
comparison using triangle sampling on both grids. Do not mix old bilinear
history with the new surface or count passing source hashes as geometric
equivalence. All owned work exited; later rivers remain queued.

## Triangle fields staged and checked in the actual engine

The corrected triangle-sampled package is now loaded in the same isolated
review map. The previous map has an exact, exclusive rollback copy; the full
terrain/collision mesh and surface material are unchanged. All 16 interior
collision probes are rechecked before saving. The staging script refuses
changed map/source/array identities or prior staging evidence. The combined
Python suite passes 26 tests plus 21 subtests; the Unreal build succeeds.

A distinct triangle-package replay regression now passes, as does actual-scene
captured-ground contact. The guided route is generated from the new fields;
runtime checks reject mismatched field path, depth hash, source or sampling.
The engine suite remains **2/3**: guided traversal reaches the outlet in
81.682 s but its 5.145 m tracking error exceeds the unchanged 5 m limit.
Single-carrier/material assertions pass, with no sampled ground penetration.
No old bilinear replay was counted as validation of the new package.

Fresh fixed-camera captures show animated foam/spray but still overly faceted
crests and marbled smooth froth. Clean performance is 18.990 ms mean / 24.632 ms
p95 over 1,054 frames; solver mean 11.274 ms. Both budgets still fail. No visual,
settling, convergence or full-route acceptance is claimed. The former
export-only status is historical, not the current loaded scene state.

A separate CPU bounds-check experiment was byte-equivalent across three native
A/B pairs, but only 1.09% faster in median including exports. It was rejected
and the pre-experiment solver code restored (only line endings differ). The engine-linked archive
and cook binary never changed. Candidate evidence is preserved, not promoted.

See [integration, captures, tests, rollback and next work](triangle-runtime-review.md).
The current review-map SHA is
`a54447bbc029acfe40dfed0cd3379e8119dab1cc49d304ead558d37b558ae7cb`.
Do not blindly rerun the old importer/generator or staging script. Continue
CPU/crest improvements or same-method fine-grid investigation; full-reach
migration and rapid identity remain outstanding. Later rivers stay queued;
no commit/push or production-map change in this pass.

Final expanded staging/route/sampling/export suite: **37 tests plus 21 subtests
pass** (`triangle-runtime-regressions-final.xml`). All owned processes exited.
The native source rollback was checked against its pre-experiment copy after
normalizing line endings; solver archive and baseline executable hashes remain
unchanged. Prior unrelated native code/test changes are preserved.

## 13:00 pass: same-triangle refinement rejected, failure localized

The controlled half-metre refinement of the triangle-sampled 1 m parent has
finished: `0.5m-mixed-inlet-mesh-triangles-refined-20260907`, 240 seconds at
dt 0.1 / CFL 0.2, 1,373.262 wall seconds. Identical geometry, triangle sampling,
physical bounds, binary and forcing were verified. Initialization changes
storage by -3.74749 m3 (-0.0222%); it is not conservative or accepted steady flow.

Independent screening rejects frame 5 (100 s): one 9.54 cm-deep bank cell reaches
23.7504 m/s, above the unchanged 20 m/s bound. All other saved frames pass, which
does not rehabilitate the history. No fine export, regional settling acceptance,
engine staging or production promotion. The rejected comparison retains all
frame hashes. The cell is at station/lateral (-20.25, -28.25) m, grid (104,230),
UTM (683834.349695056,4296692.276994233). Adjacent 80/120-second saved samples are
quiet. Reproduce this specific momentum spike with denser bounded output before
another full refinement; do not repeat/extend unchanged or relax acceptance.

The new static subgrid capacity audit finds up to 2.282 m point-sampling loss at
narrow rock edges despite only millimetres of median bed difference. It is not
a flow solve or proof of the spike's cause. Its independent regressions pass.
The newly retained CDFW 2020 memo visually documents upstream Meatgrinder/Triple
Threat at a coordinated 300 cfs target, not Troublemaker or the 1600 cfs scenario.
No new measured bathymetry or verified Troublemaker layout is claimed.

See `triangle-refinement-review.md`, `triangle-resolution-comparison.json` and
`triangle-subgrid-geometry.json`. Current Unreal review map/source/material and
engine-linked solver are unchanged. South Fork is incomplete; Colorado, Pacuare
and Futaleufu remain queued. The owned cook and comparison processes have exited.

Final regression run: **27 tests plus 27 subtests pass**. Rechecked map, native
cook executable and engine archive hashes match their pre-pass identities.

## Completion request: depth-limited hydrostatic candidate

The saved bank failure reproduces exactly in a bounded full-domain restart.
A wet-step guard, hydrostatic-only change and adaptive-CFL variants each fail
some tested history; their binaries/source and every result are preserved.
The current candidate instead uses consistent hydrostatic interfaces, each
side's cell bed, and depth-limited free-surface half-slopes in uncalibrated
MUSCL. Calibrated paths are unchanged; the adaptive timestep experiment is
reverted. Two bounded half-metre histories (0–30 and 80–101 s) pass every saved
frame and exact conservation. This is not continuous fine-grid convergence.

The fresh `1m-mixed-inlet-depth-limited-hydrostatic-20260907` cook completes
600 simulated seconds in 225.135 wall seconds, max saved speed 5.902 m/s.
All saved frames and the unchanged mean-flow/face-flux checks pass. The new
export retains offline binary SHA `1f010cbe7edce8eb579c2d9a040820a24d6ee6ac1615073e3afbf899cac9ba50`.
The original default cook binary is unchanged; explicitly select the new
binary for future matching cooks.

Three native fixtures and the native suite on actual 1 m survey geometry pass.
Fifty Python tests plus 27 subtests pass; another 23 staging/route tests plus
15 subtests pass. Three Windows/macOS package-fixture failures are fixed with
strict production validation retained and a negative execute-bit test added.
Seven editor layout/provenance failures still reproduce. See the new all-scope
queue index `docs/plans/remaining-work.md`; no earlier requested work is closed
merely by completing an isolated diagnostic.

Engine-linked archive now SHA `83f35ddf4e6ab28fc07999804e63d3ccfcd5d0d78d8f0775c96e909913910f03`;
old archive is `tmp/south-fork-bank-spike-20260907/raftsim_water.engine-before.lib`.
The full editor rebuild succeeds. The review map now loads the matching new
package/start with 16 collision probes passing, unchanged mesh/material and
map SHA `2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd`.
Rollback: `tmp/project-cleanup/SouthForkSurveyPlayable-before-depth-limited-fields.umap`.
Do not rerun prior one-off staging scripts over it.

Actual engine replay and captured-ground contact pass. The initial guided
launch in `SurveyDepthLimitedTests.log` fails preflight because PowerShell
splits the unquoted route argument before `.json`; explicitly quote the entire
`-RaftSimSurveyGuidedRoute=...` argument. The separate corrected invocation is
`SurveyDepthLimitedGuidedQuoted.log` / `engine-depth-limited-guided`. It reaches
the outlet in 98.891 s without sampled penetration but fails tracking at
12.329 m versus 5 m. Raw report `SouthForkGuidedTraversal_20260907_150623.json`.
The ledger now preserves 13 runs, including missing-report preflight failures.

Clean performance: `survey_performance_depth_limited.json`, 14.669 ms mean /
19.437 ms p95, solver 9.515 ms; still fails p95/frame and solver budgets.
Actual fixed captures `SurveyDepthLimited20260907_000..002.png` at 6/9/12 s
show angular crests and marbled/stretched foam, not photorealism. Boat-height
captures also remain too smooth. All owned processes have exited.
Final staging/route/ledger regressions: 25 tests plus 15 subtests pass.

Next: same-core fine-grid check, current-aware guided-route feasibility and
localized crest detail/performance. Keep the current candidate with its passing
offline settling/conservation; do not revert to rejected spike-producing cores
or blindly rerun old staging scripts. Source code changes affect uncalibrated
MUSCL wherever used; calibrated legacy paths are preserved, but other rivers
are not newly qualified. No full-river promotion or final commit yet. Details:
`bank-spike-fix-review.md` and `bank-spike-experiments.json`.

## Attainable-track guidance continuation

No duplicate cook or other work was running. Investigated the current raw
12.329 m guided failure, localized the slow turn at stations 34–59 m, and added
two explicit survey-only flags in `RaftSimSouthForkNaturalDriftTest.cpp`:
`-RaftSimSurveyCoordinatedSteeringReview` and
`-RaftSimSurveyAttainableTrackReview`. Use both with the existing breaking/lit-foam
flags and fully quoted depth-limited route argument. They enable normal stern
sweeps while the crew pivots and replace abrupt lateral heading demand with
the attainable 2.2 m/s effort/ground-track triangle. No steering strength,
velocity, route point, water core or asset is changed. Baseline remains available.

Coordinated-only run fails at 10.216 m, retained in `engine-coordinated-steering`.
The complete controller passes at 3.869 m / 66.980 s, then 4.712 m / 67.145 s in
the final four-test suite. Both have zero missing ground/grounded/unattainable
samples. Final minimum tube clearance 36.046 cm. Reports:
`SouthForkGuidedTraversal_20260907_153340.json` and
`SouthForkGuidedTraversal_20260907_153742.json` in `unreal/Saved/Automation`.
Final evidence: `engine-attainable-steering-combined/index.json` (4/4 pass).
The first pair of tests retains the engine MotionVectorSimulation render-thread
warning; do not suppress it or describe the run as warning-free.

Build succeeds; 12 Python checks plus 9 subtests pass. Ledger retains all 16
runs. Actual boat-height image `153340_001` still shows mostly smooth water and
plain captured terrain: no visual acceptance follows. Map, archive and field
manifest hashes remain 2c53df..., 83f35d... and 0cbd69... respectively. All owned
processes have exited. Two passes on one route/discharge are not broad robustness;
the final margin is only 0.288 m. Do not reopen the same steering failure or
re-cook the already completed coarse case unchanged. Next: same-core fine-grid
convergence, localized crest/foam shape and solver performance, then geographic
registration/full-route migration. See `attainable-guidance-review.md`.

## Active completion goal and same-core refinement

The user's explicit September 7 request successfully created the app goal for
ALL remaining work in `docs/plans/remaining-work.md`, without a token budget.
Keep it active; this numerical milestone is not completion. No old process was
running when resumed. All processes launched below are now finished.

New fine run: `0.5m-mixed-inlet-depth-limited-refined-20260907`, 240 seconds /
697.415 wall seconds, 13 saved frames. Same core SHA 1f010c..., same captured
triangle geometry and exact forcing as the completed depth-limited coarse run.
Every saved frame passes; max h 2.501368 m, speed 6.051162 m/s. Mean-flow all
three checks and exact numerical conservation pass. Crux fine-minus-coarse
stage median -1.541 cm, absolute p95 8.735 cm, maximum 25.344 cm; localized
velocity differences still reach 2.485 m/s. Two grids are not proven convergence.
Reports: `depth-limited-resolution-comparison.json`,
`depth-limited-refined-regional.json`, corresponding flow/flux reports under
September 6, and `depth-limited-refinement-review.md`.

Fine `engine_review` package exported, NOT loaded: manifest SHA 50fe1c..., depth
SHA 0d3ee8..., start [-60.25,-9.75] with 1.0033 m square-footprint minimum depth.
The actual map still uses the prior one-metre depth-limited fields, SHA2c53df...
and archive83f35d... unchanged. Do not rerun the old one-off staging wrapper;
it targets the previous map/package and would be wrong here.

`verify_south_fork_survey_flux.py` now rejects changed/missing solver binaries,
bad endpoints and overwriting existing audit evidence. Eight tests plus 18
subtests pass; the real fine audit passes through these guards. Final goal
includes all remaining rivers, crew, project maintenance and commit.

Next meaningful work: remaining localized grid sensitivity and efficient
single-surface presentation of the now-stable flow. Investigated but did NOT
change `StepWater` in `RaftSimWaterRuntimeAdapter.cpp`: it still advances the
entire native window each rendered fixed water tick (~9.5 ms on the coarse
review). Blindly loading four times as many live cells would worsen the budget.
An explicitly scoped steady-base/local-animation performance experiment may be
worth evaluating; preserve water/raft sampling, animation time, collision and
honest mode telemetry rather than silently freezing an alleged live simulation.
No new geographic evidence was validated; AW trip-report fetch was HTTP403.

## Solver scratch reuse and viewed reference continuation

No existing process was running. Added separate CLI solve/capture versus export
timings and strict parsing/tests. An isolated LTO comparison preserves all CSV
fields but improves solve time only 3.53%; LTO is NOT adopted. Then removed
repeated full-state RK copies using per-instance primitive scratch and swapped
final allocations. Six alternating wet/dry state replacements compare fresh and
reused solvers exactly. Three native CTest fixtures and five Python tests plus
six subtests pass. Three paired 100-step comparisons preserve every saved field
exactly and reduce median offline solve/capture time 17.04%.

Candidate executable `tmp/south-fork-muscl-scratch-20260907/raftsim_water_solver.exe`
SHA f4190b0d0b7b68bd6bce2dc3fb6529872034506281d5b5c4542b44384016a357.
The Unreal-linked archive and all consumers have been rebuilt successfully;
archive SHA is NOW d91b779b83c6b32d25518d4a284ed757d175758e2342a3b3649367b925a64155
(supersedes 83f35d... for current runtime). Source `solver.hpp` layout changed;
do not mix an older archive with current headers. Cook baseline exe 1f010c...
and all cooked field/map hashes remain unchanged; no re-cook/staging happened.

Four actual engine regressions pass in `engine-muscl-scratch/index.json`, two
with warnings. Guided raw report `SouthForkGuidedTraversal_20260907_175108.json`
has 4.134 m max route error, 31.685 cm min tube clearance, 62.065 s outlet time,
586 wet samples, no missing ground/grounded/unattainable samples. Historical
ledger includes all 17 runs. Actual images 175108_001..003 were inspected:
still too smooth/streaked, plain gray terrain, finite review-domain edge visible.

Clean performance first/repeat: mean frame 15.063/13.909 ms, p95 20.283/19.050 ms,
solver mean 9.380/8.997 ms. BOTH still fail budgets. Offline gain is not proven
as equivalent engine speedup. See `solver-allocation-review.md` for full details.
Build 930.27 s, existing double-to-float warnings retained. All owned engine,
compiler, native-test and benchmark processes have exited; no live session left.

Public YouTube browser playback worked for the user's ZEG1kvjNI30 reference:
reviewed paused 0:05–0:55 frames, including the 2016-06-24 title card and localized
breaking drop around 0:40–0:45. Also viewed bank-side 2XTbOCNDcZQ at 0:58/1:03,
title date 2022-07-15 (six days before NAIP). Both browser tabs closed. No media
downloaded/imported. This supersedes the old claim that the supplied video could
not be viewed, but not the missing absolute registration or continuous-motion
measurement. `reference-review.md` records observed features and limitations.
Date-matched USGS approved DAILY means: 748 cfs (2016 video), 652 cfs (2022 video),
stored in `video-date-discharge-context.json`. They are not instantaneous rapid
discharges; retain the explicitly chosen 1600 cfs diagnostic forcing.

Next: profile the actual settled live-window workload (do not assume cold offline
cost matches runtime), then reduce solver cost without freezing the flow; address
localized breaking crest/foam shape and register fixed rock controls against the
now-viewable references. The purported local GPU fluid remains analytic WPO,
not stateful simulation. Fine grid remains export-only; do not load 4x live cells
blindly. All geographic/full-route/other-river/crew/maintenance/release/commit
requirements remain active. Do not repeat the completed unchanged coarse/fine
cooks, mark this diagnostic map accepted, or close the completion goal.

## Station-labelled surface diagnosis and normal candidates

Continuation completed 2026-09-07 around 19:00 UTC. See
`surface-detail-review.md` for the evidence, flags, hashes and limitations.
This is progress, not scene/goal completion. No owned engine/compiler process
remains running after the final build. No re-cook, scene migration, commit or
push was performed.

The previous 30-second captures skipped the local crux: the image after the
upstream start was already at station +39.62 m. Added opt-in
`-RaftSimSurveyStationCaptures` to the real guided test; its JSON now records
request filenames/times/stations/laterals at 15 m spacing. Added a runtime-only
`-RaftSimSurveyNormalIsolationReview` and actual material/texture metadata.
The saved map's visible carrier is the **surface-lit translucent review
material**, not the production Single Layer Water parent. It has 1.5 m vertices
and 3 m analysis spacing. Normal texture is 1254-square, wrap/wrap, **11 mips**:
missing mipmaps were ruled out. Runtime normal override names lack the graph's
A/B suffixes; this still needs a controlled binding fix/regression, not an
unsupported claim that it caused the current South Fork screenshot.

New guided raw report suffixes (prefix `SouthForkGuidedTraversal_`, in Saved):
- `20260907_181656`: station baseline, 13 images, pass, route error 4.40 m.
- `20260907_182027`: normal disabled, 13 images, pass, route error 4.93 m.
- `20260907_182826`: texture metadata, pass, route error 4.74 m.
- `20260907_184024`: V1 procedural normal, 13 images, pass, 4.85 m.
- `20260907_184921`: V2 procedural normal, 13 images, **FAIL**, 5.10 m > 5 m.
V2 still reached outlet in 66.83 s with 29.89 cm minimum sampled tube clearance.
Do not rerun until lucky or loosen route gates. `guided-review.json` now retains
all **22** runs, including this new failure. Shader-only changes do not establish
a physics change; variable wall-frame/capture timing exposes guide fragility.

Created two separate code-native HLSL normal candidates with
`unreal/Scripts/create_survey_current_normal_review.py` (refuses overwrite),
source files `unreal/Shaders/Private/RaftSimCurrentSurfaceNormal.hlsl` and
`RaftSimCurrentSurfaceNormalV2.hlsl`. Material assets in
`/Game/RaftSim/Environment/SouthForkSurveyCandidate/`:
`M_RaftSim_LiveRiverSurface_CurrentNormalReview` and same name suffixed `V2`.
Runtime flags `-RaftSimSurveyCurrentNormalReview` / `-RaftSimSurveyCurrentNormalV2Review`
require the existing breaking-review mode; V2 takes precedence. Neither is a
default or saved-map selection. No geometry/support/flow changes. No new fluid
simulation. V1 produces broad bands and is **not suitable for promotion**.
V2's finer triangular-kernel analytic gradients look less streaked, but are not
photoreal acceptance. Creation logs and final Unreal build succeeded.

Fixed-bank game capture: `SurveyCurrentNormalV2Bank_000.png` ... `_023.png`,
24 images at requested 0.1 s spacing, fixed focus station/lateral (0,0), camera
(451.93,735.37,1090.66) cm. Viewed frames 0,12,23 individually, not continuous
playback. Whitewater still resembles broad smooth patterns; near shore has
stepped corners. This is gray captured geometry, not the production environment.
Game startup also logs the toolset `PythonTestRunner` import error; unresolved.

Clean same-build soaks, original normal / V2:
mean frame **13.930 / 13.791 ms**, p95 **19.090 / 18.988 ms**, solver
**8.961 / 8.912 ms**, GPU **6.493 / 6.478 ms**. Differences are within run
variation; **both fail** frame and solver budgets. Reports
`survey_performance_current_normal_baseline.json` and
`survey_performance_current_normal_v2.json`. No concurrent screenshot or compile
workload, 1280x720 output/87%, active RTX3060 Laptop, 5 s warmup +20 s measured.

Map SHA remains `2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd`.
Native archive remains `d91b779b83c6b32d25518d4a284ed757d175758e2342a3b3649367b925a64155`.
Reference videos/USGS/context and fine-grid export-only status from the preceding
checkpoint remain authoritative. Do not repeat completed cooks or normal A/Bs.
Next meaningful work: shoreline clipping on the actual carrier, resolved
crest/roller geometry and foam motion, settled solver profiling, and verification
of rock controls/rapid identity before full-route reconstruction/promotion.
All later river, crew, maintenance, release and final-commit work stays active.

## Continuation — original rock XY and exact shared triangle sampling

September 7, 2026, about 20:05 UTC. Full evidence and limits:
`registered-rock-review.md`. This remains progress, not completion. All owned
processes from this continuation finished; no compile/cook/game workload is
intentionally left running. Goal and ordered queue remain active. No commit
or push; no production or original review-map replacement.

The water-hidden fixed-bank frame `SurveyShoreNoCarrier_000.png` preserves the
stepped foreground gray edge. It is captured rock geometry: the source retained
selected LiDAR heights at raster-cell centres, losing true return XY. Added
`register_captured_rock_vertices.py`, `south_fork_registered_mesh.py`, shared
`south_fork_geometry_source.py`, and full-mesh `audit_registered_rock_mesh.py`.
The new irregular mesh is explicitly incompatible with raster sampling.
FBX export, cooker and field export now support `registered_triangles` with
mesh-coordinate/connectivity hashing. Legacy sampling/identity stays intact.

Fresh candidate `tmp/south-fork-rock-return-xy-candidate-v2-20260907`, mesh SHA
`4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
4,226 original returns moved only in XY, mean 0.197892 m / max 0.350932 m.
Every recorded height and non-rock vertex stays identical. 119 diagonal flips
prevent folded faces, minimum projected area 0.000702149 m². 403,200 vertices,
803,842 triangles. Every vertex and three points on every face sampled; max
error 2.05e-12 m. 1,268 one-metre hydraulic cells change, locally -1.298 to
+1.542 m at steep faces. The preceding v1 temp candidate lacks nominal axes;
retain it as evidence, do not try to sample it with the new class.

New run `tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907`
uses original corrected solver executable SHA `1f010cbe...`, same forcing/CFL/
dt/roughness and grid, but a fresh initialization and 600-second solve.
224.838 wall seconds; 13 saved frames sane. Mean-flow three checks pass, max
tail section error 1.811%; numerical conservation three checks pass, net
+0.038501587 vs measured +0.038500730 m³/s. Review/flux JSONs use the existing
September 6 output directory and unique `registered-rock-xy-20260907` suffix.
Engine fields exported; start [-60,-9], world cm
[5910.80295497,-1368.35975807,862.85756649], minimum four-metre-radius square
footprint depth 1.000878874 m. No instantaneous-flow calibration or convergence.

FBX in `unreal/SourceArt/RaftSim/SouthForkRockRegisteredCandidate20260907`.
Stage script `unreal/Scripts/stage_south_fork_registered_rock_review.py` uses
`LevelEditorSubsystem.new_level_from_template`, then imports the exact mesh,
checks 254 collision probes (all changed triangle interiors included), and
switches fields/start in the new map only. Maximum collision error 0.0020833 cm.
New map `/Game/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable`, SHA
`81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.
New mesh `/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate`.
Original `SouthForkSurveyPlayable` SHA still `2c53df65...64969bd`; it still runs
the preceding 1m depth-limited raster-triangle package. Native archive SHA still
`d91b779b...925a64155`. No solver/archive code change this continuation.

Retained failures: generic asset duplication crashed old-world GC before any
candidate saved/imported (`StageRegisteredRockReview.log`); template API fixes
that step (`StageRegisteredRockReviewTemplate.log`). First 12 game captures
`SurveyRegisteredRockBank_*` used unmatched water settings because the opt-in
review allowlist recognized only the original map/package. Added the exact
registered-rock map/package pair to `RaftSimWaterSurfaceActor.cpp`; defaults
unchanged. Both C++ builds pass.

Correct matched 12 frames: `SurveyRegisteredRockMatchedBank_000.png`–`011.png`,
fixed station/lateral (0,0), requested 0.1-second intervals, ten-second warmup.
Actually viewed 0 and 11 plus baseline V2Bank 0. Runtime log verifies V2 normal,
lit froth, shared relief and single carrier. The local edge changes but remains
angular, and foam remains smooth: **not visual acceptance**. No continuous
playback, new-map traversal or new-map settled-performance validation yet.
Do not rerun the unchanged cook or claim the first mismatched images an A/B.

Pipeline tests: 44 + 33 subtests pass (`registered-rock-pipeline-tests.xml`),
one existing affine PendingDeprecationWarning. New
`RaftSimSouthForkRegisteredRockReplayTest.cpp` checks independent field values,
registration/datum/storage and two seconds of real runtime solver stepping.
It and baseline DepthLimitedCandidateReplay pass under NullRHI:
`engine-registered-rock-replay/index.json`, 2 succeeded / 0 failed or warned.
This does not establish ground-contact traversal or visual performance.

Next useful work: resolve remaining inferred rock/bank contour shape without
moving measured returns; crest/roller geometry, foam transport and actual
stateful fluid presentation; bounded new-geometry route/contact and settled
performance checks. Keep previous guide failure and frame/solver budget
failures visible. Verify rapid identity/layout before complete route promotion.
Colorado, Pacuare, Futaleufu, broader all-scene water, crew, maintenance, release
and final commit remain unfinished under the same active goal.

## Continuation — genuine persistent GPU detail-water core

September 7, 2026, about 20:41 UTC. Previous turn classified as progress; this
turn adds and verifies an actual stateful compute path. See
`stateful-detail-water.md` for scope, limits and retained failures. Full goal
unchanged and active. No commit/push or production promotion. All owned build
and engine sessions from this pass terminated; no live process needs restarting.

New module `RaftSimWaterDetail` in the RaftSim plugin, `PostConfigInit` shader
registration. Public API `FRaftSimDetailWaterGrid` and `FRaftSimDetailWaterGPU`
in `Source/RaftSimWaterDetail/Public/RaftSimDetailWaterGPU.h`; implementation
in the sibling Private directory. Compute shader
`unreal/Plugins/RaftSim/Shaders/Private/RaftSimDetailWater.usf` mapped as
`/Plugin/RaftSimWaterDetail/Private/RaftSimDetailWater.usf`. Automation module
now explicitly links RaftSimWaterDetail, RenderCore and RHI. New tests in
`RaftSimStatefulDetailWaterTest.cpp`. No modification of the native solver
archive, current material assets or water actor in this continuation.

State RGBA is perturbation height, x/y depth-integrated perturbation momentum,
foam density. Mean-flow RGBA is depth, u, v, aeration-source strength [0,1].
Linear finite-volume gravity-wave perturbations advect over mean flow; foam
upwinds with mean velocity only. Hydrostatic local-pressure correction balances
nonzero constant perturbations over uneven depth. Dry cells <=0.01 m have zero
state; domain boundaries closed unless explicit periodic regression mode.
Source/decay is analytic for foam density (can exceed one under compression;
do not clip it as though already coverage). Momentum damping is exponential.
No height clipping or epsilon-depth velocity division. Two-dimensional CFL
<=0.45 required; max grid 512²; 1–512 steps/batch. Implicit initial-state reset,
resize, cell-size or periodic-boundary changes are rejected. `Reset` explicit,
render-thread-owned. Extracted RDG state persists across graphs. No runtime
readback; tests alone read results back.

Build failures fixed: shared-reference `.Get()` returns a reference, pointer
required `&Readback.Get()`; explicit RenderCore/RHI link dependencies added.
Existing D6 runner float warnings remain unrelated. First shader startup crash
`StatefulDetailWaterV1.log`: UE shader parameter parser cannot minify the grouped
root scalar declaration here; split into individual declarations. v2 compiles
and runs on actual D3D12 SM6 RTX3060 Laptop (not NullRHI).

Initial two GPU tests pass (`engine-stateful-detail-water-v2`). Added uneven
depth/dry island test reproduces artificial momentum 0.02792478 and height
error 0.00893691 m (`engine-stateful-detail-water-shore-before`, **1 failure**).
Corrected local pressure balance; unchanged tests pass in
`engine-stateful-detail-water-shore-balanced`. Do not erase the failed report.

Final `engine-stateful-detail-water-captured/index.json`: **5 succeeded, zero
warnings/failures**. Includes existing RegisteredRockCandidateReplay plus four
WaterDetail tests. Conservation test: foam travels exactly 2.000000 m in 1 s
at 2 m/s through two consecutive 60-step graphs; foam integral error
-1.09642e-6, height integral error 1.38628e-8, no negative foam/crest growth.
Resting uneven-depth test: zero spurious momentum, zero height error, zero dry
state; foam source/decay error 2.08616e-6. Captured-flow fixture samples actual
registered-rock fields via runtime adapter on 64² one-metre grid around crux:
2,147 wet cells, maximum background speed 5.426266 m/s. Synthetic <=5mm seed
stays <=3.52177mm after 2 s/240steps, finite, foam [0,1.498459], dry state zero.
Frozen background flow and synthetic perturbation: NOT continuously running
scene coupling, measured waves, visual acceptance or performance evidence.

No new rendered images this turn because the module is not connected to a
surface yet. Original and registered-rock map hashes remain `2c53df65...64969bd`
and `81f31bec...705ad7`. New core does not replace the old noise-function
`ComputeCoupledLocalFluidHeightfieldMeters`, which is still what that existing
path implements. No claim that GPU heightfield alone resolves overturning
crests or that numbered items 4/5/6 are complete.

Next concrete implementation: GPU texture resolve (height, slopes, foam density
to coverage), live mean-flow upload owner, persistent world-grid shifts rather
than camera resets, hydraulic/turbulence excitation, and binding to the EXISTING
single carrier. Macro stage and raft-support authority must remain consistent;
current 1.5m surface lattice cannot show sub-metre geometry without appropriate
bounded refinement. Compare actual rendered motion and settled CPU/GPU cost;
the pre-existing solver/frame budget and guide failure remain open. Continue
South Fork before ordered later reconstruction tasks; preserve full queued
water/crew/normalization/release/final-commit scope.

## Continuation: visible stateful detail, source localization and cost correction

Full goal remains active, not complete or blocked. No production promotion,
commit or push. All owned engine/build sessions in this pass are terminal.
Continue from this section, not the previous section's pre-integration status.

Implemented GPU resolve `RaftSimDetailResolve.usf` and `FRaftSimDetailWaterGPU::Resolve`:
float4 UAV output is height metres, X/Y slopes, foam coverage `1-exp(-density)`.
Slopes differentiate the edge/depth-tapered height, dry and window-edge output
is exactly zero. Persistent state now tracks fixed origin and true accumulated
simulation time; implicit origin changes rejected. Empirical source-localized
0.06m pressure fluctuations drive momentum, not direct rendered noise height.
Default pressure strength remains zero for prior fixture compatibility.

New `RaftSimStatefulDetailComponent.{h,cpp}` in RaftSimRaft is the live owner.
Fixed world-centred crux window, 128² at 0.5m, first cell centre -32m; texture
domain borders (-32.25,-32.25,64,64). Cache 65² world-to-river coordinates and
projected basis once; sample live depth/velocity at 1m eight times/second,
bilinear upsample to 0.5m. Dynamic CFL step <=1/120s, up to16 substeps/frame,
retain backlog. No runtime readback or camera reset. Refuse initialization
without live window/coordinate map; fail closed if live hydraulics disappear.
Final native guard build succeeded; the eight-test report below precedes only
that final additional guard. Native solver archive unchanged throughout.

Opt-in flags on exact registered-rock map/package:
`-RaftSimSurveyBreakingReview -RaftSimSurveyLitFoamReview -RaftSimStatefulDetailReview`.
Actor loads new `M_RaftSim_LiveRiverSurface_StatefulDetailReview` and binds component
to the EXISTING SurfaceMesh MID. No second mesh/surface. Builder script
`unreal/Scripts/create_stateful_detail_review_material.py` duplicates V2 once,
refuses overwrite, verifies map/source material hashes, default enable0.
Material custom expressions sample explicit RGBA basis/domain params, world
position excluding WPO, output vertical height*100cm and world-to-tangent slopes.
Adds transported foam color/roughness, unchanged opacity. Material created and
compiled successfully, report `stateful-detail-material-setup.json`. Both map
hashes rechecked unchanged: original `2c53df65...64969bd`, registered
`81f31bec...705ad7`. Production materials/maps untouched.

Real-GPU report `engine-stateful-detail-water-resolve/index.json`:7 passed.
Pressure fixture max height0.0470908321m, identical one/two-batch evolution,
dry0 and inactive source gives zero state. Texture fixture CPU-vs-GPU RGBA max
error5.96046448e-8, dry/edge0. Added origin/rate validation checks. Cache variant
`engine-stateful-detail-water-cached`:7 passed, includes live cached-coordinate
versus world depth/velocity agreement within1e-6.

First clean new-path timing failed/regressed: p95 30.564ms and34 >33ms hitches.
Retained `survey_performance_registered_stateful_detail.json`. Cause addressed:
repeated fixed-coordinate inversion at each live update. Cached variant:
mean13.868/p9519.016ms, zero hitches, flow prep0.414ms mean/0.709max,
backlog0.001602s at24.485s. Matched V2 baseline mean13.877/p9518.908ms, GPU6.440ms;
cached GPU6.527ms. Correct V2 flag is **RaftSimSurveyCurrentNormalV2Review**.
Earlier `survey_performance_registered_detail_baseline.json` used wrong flag
order and actually loaded SurfaceLitReview, NOT a V2 baseline. Correct report:
`survey_performance_registered_detail_v2_baseline.json`. No timing run had
concurrent captures/builds; none is packaged-release qualification.

Initial `SurveyStatefulDetailBank_000..011.png` actual capture showed too much
uniform whitening. Replaced runtime blanket-Froude source with inline pure
helper `RaftSimDetailEntrainment.h`: require wet-supported deceleration or
convergence near Froude transition. No zero-velocity invented dry neighbours;
one-sided wet derivatives. Empirical thresholds, not measured entrainment.
Only source W changes; persistent foam still advects/decays. New source fixture
uniform fast channel/shore0, localized transition1, dry0, 90deg rotation error0.
Latest `engine-stateful-detail-water-entrainment/index.json`: **8 passed**, zero
warnings/failures (7 WaterDetail plus RegisteredRockCandidateReplay).

Latest capture `SurveyStatefulEntrainmentBank_000..011.png`, inspected0,6,11:
less uniform runout whitening, but main crest still sheet-like, angular rock
outline unchanged. Not accepted. Fixed bank focus station0/lateral0, camera
451.93,735.37,1090.61cm. Initial10s hold,12frames0.10game-sec interval. No claim
of long continuous motion acceptance from sparse frames. Live logs1,198steps
at10.006s/backlog0.005834s. Existing EditorToolset AgentSkill and ToolsetRegistry
PythonTestRunner startup errors remain; no water-dispatch error observed.

Latest clean source timing `survey_performance_registered_stateful_entrainment.json`:
mean14.140ms/p9519.229ms,0hitches, GPUmean6.530ms, solvermean8.992ms.
Flow/source prep0.752ms mean,1.026max,184updates,backlog0.007600s at24.458s.
Still FAILS unchanged16.667ms frame /1.6ms solver budgets. Keep all reports.

Next meaningful work: fine crest geometry on the single carrier without
multiplying expensive hydraulic samples, macro/detail raft-support consistency,
better crest/foam breakup and longer actual animation inspection. Existing
carrier is1.5m/10,465verts; 0.5m GPU slopes alone do not create fine silhouette.
Surface actor CreateMeshSection~1953 and update~6956; a bounded refinement must
preserve UV/color/basis, wet mask and single shared macro authority. No refinement
implemented here. Fixed window is not moving-grid remapping. Still unresolved:
angular captured rock outline, geographic rapid identity/layout, guided route
failure, original solver budget, later ordered rivers and all other queue work.
See updated `stateful-detail-water.md` and `docs/plans/remaining-work.md`.

## Continuation: conforming fine carrier, verified but too costly on CPU

Previous turn classified progress (live GPU integration/source/cost correction).
This turn also progress: added a genuinely finer single-carrier mesh with
conforming edges, preserved hydraulic attributes, verified tests and measured
its actual rendered cost. Full goal unchanged and active; no commit/push,
production promotion or claim of visual acceptance. All owned sessions terminal.

New `unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimSurfaceRefinement.h`:
`FRaftSimSurfaceRefinement::Build` uses two red/green subdivision levels inside
river-coordinate [-32,32]². Shared-edge midpoints also split adjacent triangles,
avoiding T-junctions. Midpoint parent indices allow exact affine interpolation
from the existing source vertices. No new hydraulic sampling. Refinement helper
is Core-only, header-inline; tests in new `RaftSimSurfaceRefinementTest.cpp`.

Actor now routes section0 creation/update through `UpdateSurfaceCarrierMesh`.
Default branch retains the previous unrefined calls and linear-color encoding.
`-RaftSimStatefulDetailGeometryReview` only applies when the registered-rock
stateful detail flags/package already qualify. Refines section0, no extra sheet.
Caches parent topology/arrays; rebuilds if source count or first river coordinate
changes after a lattice recenter. Dynamic position/normal/UV/flow/wake/color
arrays interpolate coarse authoritative data at each existing refresh. Normals
and tangents normalize. GPU fluid origin/state do not reset. No material asset,
native solver archive or map changed this turn.

Build21actions/82.45s passed. `engine-stateful-detail-water-refinement/index.json`:
**9 passed**, zero warnings/failures. Conforming fixture tests every edge's
incidence (interior2, boundary1), winding, area, fine edge length and untouched
distant triangles, affine position/color interpolation. Area144m², plane
error4.4408921e-16m, colorerror6.51925802e-9, maxcruxedge0.530330086m,
80 untouched original distant triangles. Old8 tests also pass. Separate
`engine-water-refinement-legacy-regression/index.json`: **3 passed**:
WaterSurfaceRenders in actual dev tank, WaterDataLinearEncoding, WaterTexturePrecision.

Actual capture `SurveyStatefulFineGeometryBank_000..011.png` with all stateful
flags plus GeometryReview, fixed bank station0/lateral0,10s hold/0.10s interval.
Frame11 inspected: subtle change, main crest still sheet-like, angular rock
shoreline unchanged. Runtime source10465verts, rendered38721verts/76992triangles;
same material/surface section. Fine grid edges0.375m, diagonals0.5303m. Existing
log field `surface_vertices=10465` still reports **source**, not actual fine count;
the new `Stateful detail geometry:` line is authoritative for rendered count.
1,198GPUsteps at10.009s, backlog0.000760s. No water errors; old engine toolset
Python startup errors persist. No continuous-motion acceptance from one frame.

Clean timing `survey_performance_registered_stateful_fine_geometry.json`:
mean15.418203ms/p9522.225700ms,max27.517799ms,0>33ms hitches. GPUmean6.634601ms,
rendermean7.904216ms/p9511.359100ms, solvermean8.916ms. Previous source variant
mean14.140154ms/p9519.229400ms. Extra fine CPU interpolation/procedural-buffer
updates cost ~3ms at p95; **failed existing budgets**, no quality cuts to hide it.
One recenter in that run rebuilt topology to38980verts/77510tris. Flow/sourceprep
0.763180ms mean/1.226701max,backlog0.000153s at24.467s. Session6490 terminal0.
Build39833,capture90667,GPUtests19815,legacytests15928 also terminal0.

Next: fine geometry should retain this tested topology but receive interpolated
coarse attributes on GPU, avoiding fine CPU vertex uploads each refresh. Local
source geometry/material values must remain identical, single surface only.
Potential design (not implemented): immutable fine XY mesh, UV3 coarse-grid
coordinates, GPU textures containing coarse world position/normal/color/flow
and wake, triangle-barycentric sampling matching the original I0,I2,I1 diagonal,
WPO to current coarse surface plus persistent GPU detail. Existing UV3 is empty;
UV0 river texture, UV1 flow, UV2 wake already used. ProceduralMeshComponent's
UpdateMeshSection copies/uploads its whole vertex buffer even if optional arrays
are omitted; just passing empty UV/tangent arrays won't remove the main cost.
Engine implementation was inspected, not modified. For materials, guard
world/local transforms, float4 parameter outputs, linear data and shader stages.

This is not permission to substitute small procedural ripples for the missing
macro rapid shape. Captured/inferred bathymetry, rapid identity/layout, real
crest/foam breakup, raft-support consistency, long animation, angular rock edge,
guide failure, original solver budget and all later queued work remain open.
Updated `stateful-detail-water.md` and remaining-work index reflect this pass.

## Continuation: GPU macro interpolation and live culling bounds

Previous turn classified progress (conforming fine geometry and measured CPU
cost). This turn also progress: replaced recurring fine CPU interpolation/
vertex upload with GPU sampling of coarse authority, retained the fine single
mesh, verified shader math/rendering/bounds, and measured recovery of its added
cost. Full goal remains active. No production promotion, commit, push or final
acceptance. All owned engine/build sessions from this pass are terminal.

New flag **`-RaftSimStatefulGPUCarrierReview`**, alongside existing
`-RaftSimSurveyBreakingReview -RaftSimSurveyLitFoamReview -RaftSimStatefulDetailReview`,
only on registered-rock map/package. Implies geometry review; no need to pass
the separate GeometryReview flag. Fine topology still38,721verts/76,992tris,
coarse10465; after one recenter38,980/77,510. New actor `UploadMacroSurface`
uploads161x260 float4 atlas (4 bands, each161x65): world position.xyz, world
normal.xyz, linear RGBA hydraulic color/coverage, flow.xy/wake.zw. Atlas stored
in actor-owned `MacroSurfaceTexture`; source transforms applied explicitly.
RHI UpdateTexture2D copies CPU data into a staging allocation before returning
(D3D12 implementation inspected). CopyDest/SRV transitions explicit. No readback.

Fine mesh gets UV3 coarse-grid index coordinates (quarter-cell values, exactly
representable at this grid size); existing UV0 texture/UV1 flow/UV2 wake intact.
No recurring fine buffer updates, only coarse atlas uploads at the original
hydraulic cadence. Mesh recreated on lattice changes. Source/candidate selection
failure disables GPU-only geometry rather than leaving an unbound flat mesh.
BuildGrid clears old atlas/bounds when reconfigured.

New shared `RaftSimMacroSurfaceSample.ush`: original triangle-barycentric
(A,C,B)/(B,C,D) sampling, NOT bilinear smoothing. Material created by
`unreal/Scripts/create_stateful_gpu_carrier_material.py`:
`M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview`, defaultMacroSurfaceEnable0.
Read-only graph inventory `inspect_stateful_material_graph.py` ->
`stateful-material-graph.json` informed exact VertexColor and UV1/2 rewiring.
Both scripts use verified MaterialEditingLibrary APIs; old input output names
preserved (including alpha). WPO adds current macro-world-minus-static-world
to existing detail WPO. Normal steers the original micro/detail normal with
the sampled macro normal in tangent space. Source textures remain linear;
colors use float atlas values (not unintended sRGB). Creation report
`stateful-gpu-carrier-material-setup.json` records immutable source/map hashes.

New `URaftSimWaterCarrierMeshComponent` (RaftSimRaft/Public header) subclasses
ProceduralMeshComponent and replaces the actor's native SurfaceMesh default
subobject; without hydraulic bounds it delegates to ordinary CalcBounds.
GPU mode computes live bounds from coarse positions plus1m vertical detail
margin each upload. This prevents culling at immutable startup height.
Actual SAVED map logs `GPU macro carrier: atlas=161x260 ... dynamic_bounds=1`,
so the serialized component uses the new subclass. Resetting to ordinary mode
restores inherited bounds; tested. Initial compile failed because argument
`Bounds` shadowed USceneComponent::Bounds; renamed InHydraulicBounds and built.

Shared-HLSL regression `RaftSimMacroSurfaceGPUTest.cpp`, shader
`RaftSimMacroSampleTest.usf` registered in early RaftSimWaterDetail module.
Validation-only exported function `RaftSimValidateMacroSamplingGPU` performs
128 queries across four atlas bands, nonplanar cells/both triangle halves/
diagonal/clamped borders. GPU maxRGBAerror2.38418579e-7; a bilinear alternative
differs0.25, so it cannot pass by changing the surface interpolation model.
New GPUCarrierLiveBounds fixture tests changed stage and world transform plus
return to default bounds. Earlier `engine-stateful-gpu-carrier` has13tests
before the bounds build and is NOT bounds evidence. Final
**`engine-stateful-gpu-carrier-final/index.json`:14 successful,13 clean +1 with
warning,0failures**. Includes10WaterDetail,3P2render/data/precision,1Surveyreplay.
Warning is engine render-thread use of r.MotionVectorSimulation during actual
dev-tank WaterSurfaceRenders. Retained, not suppressed or falsely counted clean.
Intermediate `engine-stateful-gpu-carrier-bounds` has same14/onewarning result.

Actual `SurveyStatefulGPUCarrierBank_000..011.png`, frame11inspected, same fixed
bank camera. Fine water and macro profile present; main crest still sheet-like,
foreground rock outline still angular. No water shader/dispatch/culling errors
observed; engine toolset Python startup errors remain. Not continuous motion
or photographic acceptance. Map hashes rechecked unchanged original
2c53df65...64969bd and registered81f31bec...705ad7.

Clean **`survey_performance_registered_stateful_gpu_carrier.json`**:
mean14.055107ms/p9519.202999ms vs CPU-fine15.418203/22.225700ms. Rendermean7.061720/
p958.044ms; GPUmean6.597889ms. Solvermean8.905ms. One33.986805ms wall-clock hitch,
framemetricmax28.032801ms. One lattice recenter; same fine geometry and update
cadence. Recurring fine-mesh CPU cost recovered, but original16.667ms frame and
1.6ms solver budgets STILL FAIL. OffscreenDevelopment1280x720/87%screen RTX3060,
5swarmup20smeasure, no concurrent captures/build. Do not repeat this unchanged
benchmark instead of addressing the remaining macro/temporal/physical work.

After capture/timing, inspected optional-disabled material path: normalizing
a zero/default atlas could produce NaN even at lerpEnable0. Bounded repair
`repair_stateful_gpu_carrier_default.py` only changes this new material's custom
normal to a guarded reciprocal length; builder now emits that safe code.
Compiled/saved cleanly. `stateful-gpu-carrier-safe-default.json` records old/new
code and assethash dfde0cae...289d8d -> **5b43cb5d...86ad7c7ea**. This is a safe
default repair, not a claimed new screenshot improvement. Active unit-normal
data formula unchanged. Final native guards build succeeded20.40s; final14test
run after guards includes boundsreset. Final material repair session40984,
test91379, benchmark23203, capture49665 and all builds are terminal0. Inventory
session80223 returned1 despite valid JSON/clean exit log; no asset mutation.

Next meaningful issues: macro crest/foam breakup based on verified rapid
geometry/bathymetry; raft-support consistency; long actual animation and
previous-frame WPO/motion vectors. **Current dynamic atlas/detail textures have
no previous-render-frame material branch**, so accurate deformation velocities
are not established. Spatial interpolation is verified, temporal reconstruction
is not. Do not label sparse screenshots animation acceptance. One lattice-shift
hitch remains. Geographic rapid identity/layout, captured rock silhouette,
guide failure, original native solver budget, later ordered rivers and all
crew/normalization/release/final-commit requirements remain open. Updated
`stateful-detail-water.md` and remaining-work index preserve the full scope.

## Continuation: previous-render-frame water state

The preceding turn implemented GPU macro interpolation/live bounds. This turn
also made implementation progress: added real previous-render-frame textures
for macro geometry and persistent detail, created a separate opt-in material,
tested GPU frame ordering, and captured/timed the actual scene. Full goal stays
active. No production promotion, final acceptance, commit or push.

New flag **`-RaftSimStatefulMotionReview`** requires the existing registered-rock,
`-RaftSimSurveyBreakingReview -RaftSimSurveyLitFoamReview -RaftSimStatefulDetailReview`
review context and implies GPU carrier/fine geometry. New material
`M_RaftSim_LiveRiverSurface_StatefulMotionReview` SHA256
`a142f3362a039a4a03b8060634a50eb2579b2689339393a3385c4f095544f4f0`.
Baseline GPU-carrier material and both review maps remain unchanged; creation
report `stateful-motion-material-setup.json` records hashes and exact rewires.

New public/private `RaftSimWaterTextureHistory.h/.cpp` in RaftSimWaterDetail:
render-thread-owned current/previous float4 texture references, post-render
`FCoreDelegates::OnEndFrameRT` copy (engine ordering verified in
LaunchEngineLoop.cpp), explicit CopySrc/CopyDest/SRV transitions. No readback.
Copies once per rendered frame, including no-update frames, not once per solver
step. Start seeds history; explicit ResetHistory reseeds a changed macro lattice.
Rejects aliased/mismatched target dimensions/format. Stop removes callback and
releases references; owner enqueues it before shared-state release. This does
not remap previous lattice geometry or prove invisible recentering.

Actor adds PreviousMacroSurfaceTexture/MacroHistory, binds
PreviousMacroSurfaceAtlas, seeds on Create/rebuild, releases on EndPlay/BuildGrid.
Detail component optional Initialize boolean adds PreviousSurfaceTexture and
render-state History; binds PreviousStatefulDetailTexture and unregisters on
EndPlay. Original/default paths do not start history callbacks. Both saved-map
histories actually logged 857 snapshots in the lit capture and clean teardown.

`create_stateful_motion_review_material.py` duplicates the previous GPU material,
never overwrites it. Adds PreviousFrameSwitch nodes for macro position band0
and detail float4 samples. Other shading receives the current branch. Enables
output_translucent_velocity, disables is_translucency_velocity_from_depth.
No global renderer setting changes. Defaults remain optional/off.

Build session6099 completed 25 actions/84.14 seconds. Material creation91502
exit0, compiled/saved cleanly. `engine-stateful-motion-history/index.json`:
11 clean passes; new RenderedFrameHistoryGPU tests six RGBA states: bootstrap,
two updates without a rendered frame, end-frame, zero-update frame, topology
reset. Maximum error0; two explicit frame captures; target validation and
idempotent Stop verified. Test77179 exit0. Subsequent legacy tests20021 exit0,
`engine-stateful-motion-legacy-regression/index.json`: four successful checks,
three clean + the retained `r.MotionVectorSimulation` render-thread warning
in WaterSurfaceRenders. Combined15 successful/14clean/0failures. No thresholds
weakened; these are not full visual acceptance.

`SurveyStatefulMotionBank_000..011.png`, capture16726 exit0; frame11 inspected.
Main crest remains sheet-like and foreground rock edge angular. The velocity
inspection92333 used wrong token `viewmode buffervisualization`, so its
`SurveyStatefulMotionVelocity_*` are ordinary lit screenshots, NOT evidence.
Correct token from ShowFlags.cpp is **`viewmode VisualizeBuffer`**. Corrected
run71517 exit0 generated `SurveyStatefulMotionVelocityBuffer_000..002.png` with
`r.BufferVisualizationTarget Velocity`; frame1 inspected. It has 4,685 pixels
RGB(127,128,0), bounds x0..302/y302..478 in the crest area; stationary background
RGB(127,127,0). Frames0/2 uniformly quantize to the latter. This is a low-precision
smoke signal, not quantitative velocity validation. Active CVars read as
EnableVertexDeformation2/VelocityOutputPass0, i.e. default automatic WPO velocity.
Corrected run logged882 snapshots per history. Engine toolset startup Python
errors remain unrelated. No altered/debug-generated image passed as a scene.

Clean performance72286 exit0:
`survey_performance_registered_stateful_motion.json`: mean13.974982ms,
p9519.064301ms, GPUmean6.823245ms, solvermean8.891713ms. One wall-clock hitch
33.875797ms. Same 1280x720/87% RTX3060 Laptop, Development offscreen,5s warmup,
20s measure, no concurrent build/capture. Previous no-historyGPU baseline
14.055107/19.202999ms/GPU6.597889; do not infer a speed gain from small timing
variation. Original16.667msframe/1.6mssolver budgets STILL FAIL.

All owned sessions above are terminal; process check found no UnrealEditor-Cmd.
Documentation/state index updated. Next meaningful work remains macro crest
shape/froth, actual long motion and quantitative velocity validation, shared
raft support, angular captured rock silhouette/geographic rapid identity and
layout, full registered-map guided traversal and CPU solver budget. Macro
history resets rather than remaps at recenter; coarse hydraulic mesh updates
remain ~15Hz, with no temporal interpolation. No unchanged test/benchmark rerun
needed without a new implementation change. Later ordered rivers and all other
queued crew/normalization/release/final-commit requirements stay open.

## Continuation: one final foam coverage authority

Previous turn was progress (rendered-frame history). This turn also progress:
removed stacked coarse/GPU whitening in a separate opt-in material, corrected
the first too-sparse implementation after actual captures, verified graph
ownership/displacement invariants, and measured the corrected scene. Full goal
still active; no production promotion, commit, push or photographic acceptance.
All owned processes from this pass are terminal.

Inspection ruled out optical smoothing as this candidate's cause: its actual
log has smoothing0/strength0, standing scale0, relief scale1. Other production
paths still use multi-pass smoothing; do not apply that diagnosis to this map.
The existing added GPU foam coat sat on the parent's coarse foam and could only
add whitening. Current material now replaces FINAL coverage inside the fixed
detail domain, retaining old coverage outside its four-metre ownership border.

New flag **`-RaftSimStatefulFoamReview`** plus existing registered-rock gates
`-RaftSimSurveyBreakingReview -RaftSimSurveyLitFoamReview -RaftSimStatefulDetailReview`.
Implies motion/GPU carrier/fine geometry. New local bool in BuildGrid selects
`M_RaftSim_LiveRiverSurface_StatefulFoamReview`; detail component initialization
allowlist includes it. No new solver, terrain, collision, geometry or clock change.
Native build47140 completed four actions/22.58sec. Original motion material
SHAa142f336...095544f4f0 and registered map81f31bec...df705ad7 rechecked unchanged.

Builder `create_stateful_foam_review_material.py` now creates corrected version
from MotionReview. Scalar custom expression uses the same world/grid mapping as
detail sampling, distance from outer cell centres (half-cell0.25m), and4m fade:
`saturate(Base*(1-ownership)+Detail.w)`. Base is the legacy FINAL foam clamp,
not raw aeration. Detail.w already has resolve edge/depth fading, so it is not
multiplied by ownership again. Only optical coverage bounded, not density mass.
Three original final-coverage consumers (color/roughness/opacity) rewired.
The two additive custom coats are bypassed. Old lace still varies foam tone
and roughness, not the simulated fractional coverage a second time.

First material setup25620 exit0, report`stateful-foam-material-setup.json`, hash
31985a10309688cd035c084d49b29833887aeb28366c71d2cad1887c55610e4e.
It replaced raw RGB.r, so the old lace/web gate then discarded too much actual
coverage. Capture55442 exit0, `SurveyStatefulFoamBank_000..011` frame11 inspected:
too sparse, not accepted. Bounded repair `repair_stateful_foam_coverage.py`
restores those3 raw RGB consumers and replaces final clamp instead. First repair
30873 exit1: Clamp input is unnamed (`None`), not `Input`; no asset save occurred.
Corrected95027 exit0, compiled/saved current asset SHA
**9cd016469d473916bf9758c8e22568ec14fe4b36ff2a6e18d94457e028190527**.
Repair report`stateful-foam-coverage-repair.json` records code/hash/rewires.
Builder's corrected fresh-creation report name is
`stateful-foam-material-v2-setup.json`; it was not rerun against existing asset.

Read-only `audit_stateful_foam_material.py`, report`stateful-foam-graph-audit.json`:
all3 properties reach one scalar coverage; old final clamp's ONLY consumer is
the new coverage node; additive coats unreachable; WPO graph matches retained
motion baseline;2 PreviousFrameSwitch nodes/velocity flags intact. Report passes.
Process32403 returned1 despite successful audit and no logged Python/shader
errors (same observed behavior as earlier read-only graph inventory). Preserve
that qualification, do not claim a clean process or15new engine test passes.

Corrected capture39960 exit0, `SurveyStatefulFoamFinalBank_000..011` frames0,6,11
viewed: duplicate downstream whitening removed, but main crest STILL sheet-like,
foreground rock edge angular. Sparse screenshots not continuous-animation proof.
No full scene acceptance. Native/GPU physical core tests from previous pass
remain unchanged, not rerun just to accumulate checks.

Clean benchmark93211 exit0:
`survey_performance_registered_stateful_foam.json` mean13.964790ms,
p9519.026800ms, GPUmean6.819145ms, solvermean8.873544ms, one33.469101mswallhitch.
Same1280x720/87%RTX3060Laptop Development offscreen5swarmup20smeasure, no concurrent
build/capture. Effectively similar to motion baseline13.974982/19.064301ms.
Original16.667msframe/1.6mssolver gates remain failed, not packaged qualification.

Reference follow-up: `troublemaker-reference-followup.md`. ARR and American
Whitewater Expeditions descriptions support the upstream boulder garden/drop/
left-side S-channel/Gunsight narrative, but use substantially the same wording
(ARR credits Coloma Club), not independent surveyed-layout confirmation.
AW hazard101824 direct open403. County Upper Canyon PDF exceeded web14.3MBsize
limit; direct download access denied; screenshot unresolved. No PDF obtained or
visually inspected, no candidate identity/layout flags changed. PDF skill read
and announced but retrieval failed; no PDF authored/edited. Temporary directory
tmp/pdfs/south-fork-county-map-20260907 is empty. Do not retry unchanged blocked
URL or treat search snippet as map registration. Use accessible independent
cartographic/landmark evidence for the next geographic check.

Next substantive issues remain the physically shaped crest (macro lattice still
1.5m; fine mesh interpolates macro shape and adds small persistent perturbations),
shared raft support, long actual animation/quantitative velocities, surveyed
rapid identity and rock silhouettes, guided-traversal failure and CPU solver
cost. Do not keep fixing color as a substitute for missing 3D crest geometry.
Full ordered river/crew/normalization/release/final-commit queue remains open.

## Continuation: continuous shared crest on the fine carrier

This turn was substantive progress, not completion: measured the actual crest
sampling loss, implemented GPU reconstruction of the same support field, then
corrected its normal decomposition after close-up comparison. Full goal active;
no production promotion, later-river start, commit or push. All owned processes
listed below are terminal. Detailed record: `stateful-fine-crest.md`.

One-shot `-RaftSimCrestSamplingAudit=ABS_JSON_PATH` at world>=10s:
74,600 quarter-cell samples over2,984 wet cells; maximum coarse interpolation
error0.184039531m, RMS0.004723651m, maximum shared crest0.545408249m, worstpoint
station8.250305/lateral−0.75. Six mature sites. Report
`stateful-crest-sampling-audit.json`. The earlier0.022m strongest-site startup
log did NOT represent the mature maximum; do not use it to dismiss geometry.
Audit excludes mean/pocket/boil/GPU perturbation. Baseline capture31670 exited0,
`SurveyStatefulCrestSampling_000..002`,frame2 inspected. Build81304 exit0.

New opt-in `-RaftSimStatefulCrestReview`, requires registered-rock/detail/breaking
gates; implies FoamReview/Motion/GPU/fine. Atlas161×262 now has two rows of
physical site metadata, coarse crest centimetres in band0.W and shore weights
in band1.W. Fine WPO substitutes continuous same-field crest for interpolated
coarse component exactly once. Current/previous atlases retain their OWN sites.
No runtime readback or new physical amplitude; invalid legacy sites/overflow
log an error and retain coarse shape. Conservative bounds include crest margin.
Shared HLSL `RaftSimCrestSurfaceSample.ush`; GPU validation helper has an optional
crest mode, existing default macro triangle tests unchanged.

Initial implementation used total smoothed normal plus differentiated height
correction. Close-up paired captures33875 atstation8 (both exits0) exposed a
reflection crease: removing a triangle derivative from a smoothed normal is
inconsistent. Corrected existing wet-neighbour normal pass now omits the shared
crest in this review mode, and the vertex interpolator adds FULL analytic crest
slope. Heights unchanged. Failed compile briefly referenced out-of-scope wet
mask in UploadMacroSurface; corrected before build23536 exit0,5actions24.55s.

Current material `M_RaftSim_LiveRiverSurface_StatefulCrestReview` SHA
**52194d117dd2f21b55df3dd160526d05948b6bb564346ebeb1c947d5f858438f**.
Builder`create_stateful_crest_review_material.py` now creates corrected version.
Initial setup40873 exit0 generated SHA22ee21bb...a6534fc and a transient missing
normal-input compile warning while wiring; initial game capture88373 exit0 had
no fallback, correctMID/atlas and948history snapshots. Its old graph audit39538
exit0. Initial tests15804 exit0:12clean. Initial cleanperf95655 exit0:
mean14.225076/p9519.356300ms, retained as FIRST normal version, not current.

Bounded normal material repair54542 saved current SHA but process exited1 despite
no Python/material compile errors and a valid repair report. Qualification is
preserved. Fresh tests58665 exit0: `engine-stateful-crest-normal/index.json`,
16success(15clean+existingr.MotionVectorSimulationwarning),0fail.1,404GPUqueries
against existing CPU support oracle: maxheight7.8605739e−5cm, maxslope1.89712889e−5,
sourcevertexchange0cm, recovered21.8037663cm. Covers full/correction derivatives,
rotated/shearedXY, local/global caps, changedsites, zero sites and shoreline.

Final sequential83168 allthreeexit0: saved normal graph audit, actual crux
capture, clean benchmark. `stateful-crest-normal-graph-audit.json` passed:
current/previous distinct bindings, vertex-only slope, unchanged foam color/
roughness/opacity graph and2PreviousFrameSwitch nodes. New audit requiresfalse
argument for full slope. `SurveyCrestNormalFinal_000..011` frames2/11 inspected:
ridge STILLvisible, large aerated face STILLtoo smooth/sheet-like. No material
fallback/rejectedsites logged. Do NOT claim all reflection stripes eliminated.

Current `survey_performance_registered_stateful_crest_normal.json`:
mean14.350345ms,p9519.443399ms,GPUmean6.904082ms,solvermean8.930903ms,
one35.110001mswallhitch. Same1280×720/87%RTX3060Laptop Development offscreen
5swarmup20smeasure, isolated. Original16.667msframe/1.6mssolver gates FAIL.
No speedup/release qualification. Registered/original maps and native solver
archive hashes checked unchanged. No additional reference acquisition this pass.

Next meaningful work: resolve the remaining crest ridge/sheet appearance,
continuous motion (not more sparse screenshots), shared detail perturbation/raft
support consistency, actual rapid identity/rock silhouettes, robust traversal
and CPU solver cost. Fine analytic resampling is now implemented/tested; do not
restart that design or repeat unchanged cooks/benchmarks. Later ordered rivers,
all-scene/crew/normalization/release/final-commit requirements remain open.

## Continuation: detail transport and continuous motion review

Full goal remains active. All owned build, engine, recording, decoder and test
processes from this pass are terminal. Detailed evidence and retained failures:
`detail-transport-motion.md`. No production promotion, later-river start, commit
or push; registered map, crest material and native solver archive hashes remain
unchanged.

Implemented opt-in `-RaftSimSecondOrderDetailReview`: same fixed 128x128, 0.5m
domain and 0.06m forcing; MC-limited wave reconstruction with SSP-RK2 transport.
Source/damping splitting occurs once per full step. Changing scheme on populated
state requires explicit reset. This remains a linear perturbation heightfield,
not an overturning fluid simulation. Two foam reconstruction trials failed the
unchanged 2mm centroid-travel gate and are retained. Final foam spatial transport
stays first-order upwind; only wave xyz receives face reconstruction.

Same-grid analytic GPU wave RMS reduced from0.00724448218m to0.00106045297m,
amplitude0.0178457759m, foam travel2.00000013m. Final expanded engine report
`engine-detail-second-order-final/index.json`:17success (16clean+1existingengine
warning),0fail. Forced full/split batch error0, max response0.0508176647m, dry0.
Builds49951/83341/57328 and final test process57328 exited0. Failed trials3004/
72228 exited0 despite failed reports; do not count their process codes as passes.

CaptureSeries now supports `record` using the existing WMF recorder and fails
explicitly if recording cannot start. Final explicit-pose parser requires five
numeric pose arguments. Actual paired process17469 both exit0: baseline video
`unreal/Saved/VideoCaptures/RaftSim_20260907-184202.mp4` (696source frames,23.830s)
and candidate `RaftSim_20260907-184257.mp4` (696source frames,23.855s). Normal raft
drift, fixed station8 side camera, no teleport/paddling. Encoded 30Hz is NOT FPS.

Pinned local PyAV16.0.1 in ignored `tmp/water-motion-review-deps`; no global
dependency change. `analyze_detail_motion.py` decoded all715/716 encoded frames,
checked monotonic timestamps, saved unmodified1/8/16/23s frames and per-frame ROI
metrics under `detail-motion/`. Candidate8s/23s and baseline8s images inspected.
The broad foam face STILL looks smooth/sheet-like and spray like detached puffs.
Foam spatial gradient0.967849->0.968464 and adjacent-frame change1.059740->1.061996:
no demonstrated visible improvement. Full-stream numerical analysis is not a
claim of having visually watched every frame, nor physical velocity validation.

Isolated `survey_performance_detail_second_order.json`:mean14.377541ms,
p9519.499399ms,GPU6.920129ms,solver8.970651ms,one34.775997mswallhitch.
Same1280x720/87% Development offscreen target, no concurrent recorder/build.
Original16.667msframe/1.6mssolver gates FAIL. No speedup or release qualification.
Final logged detail backlog0.005910s; recording itself is not a benchmark.

Next meaningful visual work: aeration production, resolved height and spray
coupling at the actual crux; do not repeat unchanged transport tuning, cooks or
benchmarks. Geographic identity/rock silhouettes, shared detail/raft support,
robust traversal, CPU solver cost and the rest of the full queue remain open.
Search-only uninspected geographic leads: AWE2015 brochure PDF (camp coordinates
are NOT rapid coordinates), ARTA2025 printed South Fork map and RiverBrain run264.
No geographic identity flag or surveyed layout was changed on that evidence.

## Continuation: registered spray carrier integration

Previous turn: progress (transport implementation/motion evidence and checkpoint).
This turn also progress: fixed two actual spray integration mismatches, retained
failed intermediate capture, added regression coverage and new continuous engine
evidence. Full goal active, no promotion, later-river start, commit or push. All
owned processes below terminal. Full record `registered-spray-carrier.md`.

`RaftSimSouthForkBallisticSpray` was restricted to old FullReach in BOTH asset
selection and source anchoring. Shared `IsSouthForkSprayReviewMap` now also
recognizes only SouthForkRegisteredRockPlayable, with tested numeric PIE/package
forms. Still opt-in, unchanged existing Chilko profiles and budgets. Initial
build15253 exit0, four clean tests96316 exit0. Initial capture53049 exit0 selected
assets but rejected ALL6sites: query required visible legacy volume core. Video
`RaftSim_20260907-191730.mp4` retained as FAILED intermediate, not final.

`SampleVisibleCarrierAtRiverCoordinates` now recognizes actual visible main GPU
carrier with existing atlas/section, samples its source vertices with actor
world transform, replaces coarse shared crest with same atlas-metadata physical
profile once, preserving scale/shore weight. Existing wet/depth/buried bank and
five-point footprint checks remain. No GPU readback/new terrain queries. Does
NOT include GPU perturbation height or prove per-particle collision/landing;
continuous analytic query also differs slightly from rasterized fine triangles.

Build84439 exit0. Corrected capture38552 exit0, logRegisteredSprayCarrierMotion,
video`unreal/Saved/VideoCaptures/RaftSim_20260907-192406.mp4`:696sourceframes23.843s,
715decodedframes. At10s6published/ranked,3emitting: (7.5,-3),(7.5,3),(13.5,-7.5),
carrierZ6.804/7.540/6.475m. Other3footprints rejected, not watered down gates.
Existing decoder saved1/8/16/23s unmodifiedframes/perframeROIunder`detail-motion/`.
8s candidate and priorsecondorder8s visually inspected: foam STILLsmoothsheet,
spray STILLpuffy. No photographic acceptance or FPS inference from encoded30Hz.

New CPUanchorfixture `RaftSim.M4.VisibleSprayCarrier`:bothtriangles,transform,
exactoncecrest/shoreweight,hiddenlegacy,dryweighted/zeroweightcorners,buriedbank,
outofdomain,hiddenmain,missingatlas. Build73912 exit0,21actions82.52s. Tests13789
exit0 `engine-registered-spray-carrier/index.json`:5clean,0fail. Includesmapgate,
sourceplane,classifier,Chilkoassettest. `WaterDetail.Crest` filter matchedNONE;
actualGPUnameSharedFineCrestGPU,unchangedshadernotrerun/noGPUtestclaimthispass.

Clean isolatedperf28338 exit0:`survey_performance_registered_spray_carrier.json`,
mean14.021158,p9519.111999,GPU6.880067,solver8.919443ms,one33.896999mswallhitch,
detailbacklog.003400s. Same1280x720/87%Developmentoffscreen5+20s. Original16.667/
1.6msgatesFAIL; no robustspeedup or packaged qualification. Recordedexisting
experimentalenginePythonAgentSkill/PythonTestRunnerstartup errors, not repaired.
Registeredmap81f31bec...df705ad7,crestmaterial52194d11...858438f,nativearchived91b...
a64155 hashescheckedunchanged.

Next concrete visual investigation: resolvedGPUheight/slope under broadfoamface
versus entrainment source/coverage; no repeated obsolete-map diagnosis or
unchanged transport trial. Fine GPU spray landing/support coupling, actualrapid
identity/rocksilhouettes,robusttraversal,CPUsolvercost and full queue remain open.

## Continuation: actual GPU detail height measurement

Previous turn progress: fixed two spray integration mismatches and verified new
anchor fixture/capture. This turn progress: measured live paired GPU state and
resolved surface, establishing that added relief really is small under simulated
foam. Full goal active. All owned processes terminal. No physics/material/asset
promotion, later-river start, commit or push. Record `detail-height-audit.md`.

Non-Shipping opt-in `-RaftSimDetailSnapshot=ABS_PREFIX` requests10/15/20s snapshots
through existing component. Newprivate`RaftSimDetailSnapshot.h`:asyncbuffer+
texturecopies,polledwithoutwait,restoreSRV,nooverwriteofpending,logfailteardown.
SavesJSON+rowmajorfloat4flow/state/surfacebinaryarrays. Ordinaryplay noallocation/
readback/statefeedback. Diagnostic writing onrenderthread excludesperformance
qualification. AddedGPUclockgetter. Initialbuild64271exit1loggingmacroelse
braces;fixednextbuildexit0,5actions8.65s.

Engine75363exit0 withcurrentregistered/crest/secondorder/ballistics,existing
CaptureSeries12/3/10,no recorder. `DetailHeightAudit.log` confirmsall3saved:
`detail-snapshot/live_00..02` atelapsed10.000741/15.014790/20.010109 approximately;
exactmanifesttimestampsauthoritative. Simclock10/15.008/20.008s. No forcing,
damping,meanflow,source,grid,geometry change. Pythonanalyzerexit0:
`analyze_detail_snapshot.py`, `detail-snapshot/analysis.json`; validates sizes,
finiteness,foamnonnegative,boundsandCPUindependentresolveerror<1e-5allchannels.
Firstsampleheight/slopeerrors<4e-9,coverage<1e-7. Texturedoesnotloseperturbation.

Full-weightinteriorfoamcoverage>.65:108/125/126cells;medianabsoluteaddedheight
2.276/2.211/2.614mm,p9517.406/17.560/16.383mm,RMS8.169/7.210/8.856mm.
Medianinstantaneoussource0inallthreefoamgroups. Firstsource>.3group195cells,
heightRMS20.676mm;6600wetinteriorRMS4.108mm,max80.640mmnotrepresentative.
Densefoam>.9only6/9/10cells. Commonfoamcellsfive-secondheightdeltaRMS9.664/
14.227mm,NOTfrequencyspectrum/velocity/energy. Detailcenterstation0/world0,
NOTimagepixelROI. Doesnotincludesharedmacrocrest(previousmax.545m).

Separate41712exit0BaseColorVisualizeBuffercapture,confirmedcommandinlog
DetailBaseColorAudit. SavedScreenshots/DetailBaseColorAudit_000.pnginspected:
broadgrayvariation,notdirectfoamcoverage. DoNOTlabelalllitwhitepixelsfoam.
Finaltests87316exit0 `engine-detail-snapshot/index.json`:15clean,0fail,13GPU
detail/history/crest/resolve+2map/visiblecarrier. No new performance claim.

Next: isolate FINALmaterialcoverage versusreflectionatbroadface,thenpersistent
surface-coupledchurning/particlelandingwithactualsurface/velocityandbounded
budgets. Do not repeattransporttuning orraiseforcingboundarbitrarily. Official
SideFXwhitewatersolverHTMLreadthispass:secondaryparticlescoupletoliquidvelocity/
surface,gravity,advection,attachment,densitybehavior;referenceonly,notimplemented
Houdiniintegration. ETH2007/RWTH2018PDFsearchhitsNOTopened/read. Geographic,
raftsupport,traversal,CPUcost,allrivers/crew/normalization/release stillrequired.

## Continuation: final foam provenance and independent drift-coat removal

Previous turn progress (pairedliveGPUheight measurement). This turn progress:
isolated finalmask,foundremainingindependentdriftcoat,implementedscopedoptical
candidate,verifiedsavedgraph+actualmotion. Fullgoalactive,noacceptance/promotion/
later-riverstart/commit. Allownedprocessesterminal. `foam-provenance-optics.md`.

Build58343exit0,setup60530exit0:diagnosticM_StatefulCrestReview_CoverageAudit,
flagRaftSimCoverageAudit,sameWPO/history,UnlitRGB=final/coarselegacy/GPUfoam.
Capture67960exit0,FinalFoamCoverageAudit_000inspected: broadfacemagenta/pink,
actualfinal+GPUfoam,notmerelyreflection.Green=oldcoarsemask,notextraDriftcoat.
NoRGBlinearquantificationfromtonemappedimage. Source52194d...858438funchanged.

Read-onlygraphaudit24170exit1despitevalidreport;followups15779/20727exit0.
Maincolor/roughnessusefinalfoam,butextraDriftcoatstillindependentlyfeedscolor/
roughness/glow. Priorclaimofcompleteoneopticalauthoritytoo broad. Savedglow
defaultsnonzeroBUTcurrentSurveyLitFoamReviewsetsbothzeroalready; no newselflit
diagnosis. Reportfoam-consumer-graph.jsonincludesdirectparentaudit/refraction.

NewRaftSimUnifiedFoamOpticsReviewselectsM_StatefulCrestReview_OpticsReview SHA
25c159d5d5c5193c04a7d101dd50b63e95baf2257e802853a2ab38f525cc894b. Gateextra
driftby1-ownershipinsidefixedGPUwindow;sameworld/basis/domain/enable/border4m
fadeasfinalfoam;outsideunchanged.Finalfoamnotrepainted.NoWPO/normal/opacity
change. Initial14215exit0withPythonerrorrefusedfourthconsumer,noassetsaved.
FourthLerp43Alphaoutsideactualcolor/rough/glowtrees,notrewritten;refraction
savedrootnull,unrelatedpurposeunproven.Scopedonly3liveparents123/124/125.
Build44372exit0;setup20304exit1despitesavedcandidateandvalidinvariantreport.
Fresh-load47267exit0`unified-foam-optics-audit.json`passed:exactownershipformula,
sameinputs,3opticalconsumers,preservedWPO/normal/opacity,2historyswitches.
No freshfullautomation-suiteclaimthispass.

Capture76423exit0,labelUnifiedFoamOpticsMotion,videoRaftSim_20260907-203651.mp4:
696sourceframes23.930s/718decoded. Decoderexit0,detail-motionoutputs1/8/16/23s+
fullnumerics.8/23simagesinspected:independentflecksremoved,butfoamSTILLsmooth,
surroundingwaterexposesmoreunderlyingsmoothness,spraySTILLpuffy.No realism pass.
FoamROIgradient.74654vs.99312,darkwaterMAD.05777vs1.59645:patternremovalnotfluid
velocity/energy/FPSmeasurement.No claimvisuallywatchedeveryframe.

Perf3583exit0`survey_performance_unified_foam_optics.json`,same1280x72087%RTX3060
Developmentoffscreen5+20isolated:mean16.200989,p9521.699499,GPU6.904269,
solver9.573585ms,onewallhitch,detailbacklog.007232. WORSEthanpriorp9519.112;
16.667/1.6msgatesFAIL.No causalblameforwholeCPUincrease,no rerununtil lucky.

Nextimplementationmustaddresspersistentchurningrelief/foamandsurfacecoupled
spraywithactualliquidvelocity,surface,boundedforcing/energy,andraftsupport.
DoNOTrepeatmask/reflection,glowdefaults,ortransporttuningdiagnoses. Optical
candidateisconsistentbutnotphotorealaccepted;remainoptin.CPUcost/geographic
identity/rockshape/traversalandfullorderedqueueopen.No newresearchthispass.

## Continuation: bounded advected activity memory

Progress, not a blocker or acceptance. Full goal remains active. All owned
processes terminal. `activity-memory-review.md` records implementation and
evidence. No new research/skills/subagents, no commit or later-river start.

New opt-in `-RaftSimActivityMemoryReview`: persistent float A on the existing
128² half-metre GPU detail grid. Intensive incoming upwind transport preserves
constants under compression; exact source*(1-A)-decay*A after RK2 blend.
Runtime source=entrainment*1/s, decay=.5/s. Pressure excitation becomes
instantaneous+(1-instantaneous)*A. Unchanged .06m head/.1m accepted bound,
no extra foam source, visible surface, height clipping, or raft readback.
Authored activity persistence, NOT measured TKE/energy-conserving turbulence.
Static shader permutation removes activity resources when disabled. Advance
has optional initial/readback activity parameters; rejects implicit reseeding
or mode changes. Existing callers unchanged.

Initial build84100exit1: TSharedRef.Get() returns references, test needed
addresses for readback pointers. Corrected; subsequent buildexit0. Also fixed
source-decay metric logging to retain the correct fixture result.
Tests51794exit0 `engine-activity-memory/index.json`:16clean,0warnings/fails.
New ActivityMemoryGPU: travel2.000000133m, integralratio1.000000263,
range0..338663816, compressionconstant error0, source-decay1.27814494e-6,
split state+activity bit-identical, memory-only pressuremax.0770414174m with
zerofoam. These synthetic checks are not live-scene amplitudes/acceptance.

Capture83100exit0 ActivityMemoryMotion.log, video
RaftSim_20260907-214112.mp4:695sourceframes23.991s/720decoded. Same map and
unifiedfoamoptics candidate, all prior flags plus activity. Paired diagnostic
snapshots10/15/20s in activity-snapshot, independentresolve<1e-5, allfinite,
foamnonnegative/coveragebounded. No activitybuffer captured. Analyzer accepts
--directory now to preservebaseline. Foamyfullweightcells108/125/126:
medianaddedη6.141/4.629/4.884mm, p9522.440/20.833/26.150mm,
RMS10.981/9.275/11.973mm; earlier baseline median2.276/2.211/2.614mm.
Sparse slightlydifferent samplingtimes, addedGPUheightonly. Temporaloverlap
RMS13.049/18.161mm notfrequency/energy. 8/23s decodedframes inspected:
broadfoam STILLsmooth, spray STILLpuffy/detached-looking. No visual pass.

Separate no-record/no-snapshot performance84717exit0:
survey_performance_activity_memory.json, same1280x72087%RTX3060Laptop,
Developmentoffscreen5warmup20measure. Mean14.317660,p9519.435900,
GPUmean6.888019,solver9.000088ms,onewallhitch. 16.667/1.6msgatesFAIL.
Prior optics p9521.699/solver9.574; not evidence memory made CPU faster.
No packagedqualification/retryuntilpass. All work stays opt-in.

Next: still needs realistic surface-coupled foam/spray and CPU cost reduction,
not another coverage audit or arbitrary forcing increase. Read-only CPU
orientation this pass: solver metric wraps LiveWindow->Step in
RaftSimWaterRuntimeAdapter.cpp:133; includes live-window work, not merely the
native numerical step. Inspect/profile that boundary before attributing the
whole9ms to the native FV kernel. No new CPU profiling code yet, nativearchive
unchanged. Geography/rockshape/registeredtraversal/support/fullqueue open.

## Continuation: native stage profiling and integrated primitive reuse

Previous turn progress (activity memory). This turn progress: measured native
stages, reduced repeated primitive reconstruction, integrated timer-free archive,
measured actual engine improvement and corrected stale guided-test setup.
Goal ACTIVE, no acceptance/promotion/commit. All owned processes terminal.
See `native-stage-profile.md` and `native-stage-profile/` reports. No skills,
research or agents this pass. Do not treat the route failure as a blocker.

LiveWindow::Step inspection confirms only native Solver->step plus counter;
the9ms adapter timing is not field export. Added default-OFF CMake
RAFTSIM_PROFILE_SOLVER and private solver_profile.hpp compile-time scopes:
FVtotal/CFL/reconstruction/flux/combine-friction/recompute, inclusive walltime
perthreadstderrJSONatthreadexit. No API/ABI changes or normal-build timers.
New physics/scripts/profile_registered_solver.py: isolated600steps at1/60s,
originalregisteredscenario boundaries, actual exportedfloat32h/u/v/bed→double,
sameconfig, freshoutputonly. Checks manifest hashes/boundaries. First attempt
failed NPZ h vs requireddepth before stepping; fixed and failure retained.

Baseline profile Release total8.374649ms/step:27.2%reconstruction52.5%flux.
Isolated CMAKE_INTERPROCEDURAL_OPTIMIZATION=ON7.580347ms; no productionIPO.
Sourceoptimization: local immutable-RK-stage vector of MusclFaceState stores
h/eta/u/v once, reused for slopes/faces. Positivefilms preserved, no crossstage
state, no numerical/resolution/timestep/friction/boundary change. Extra~1.4MB.
WithIPO6.891147ms,without7.398085ms. AllfourfinalCSVhashidentical
7934382caa29e210eda346212eb82c8b838a620c6736bd74cd34aedcf5541109.
One run/config, not confidenceintervals. All3nativeCTest pass forIPO+ordinary
and after rebuilding ordinary with timersOFF. Logs retained. Baselineexe in
profilebuilddirectory overwritten by laterbuilds, hashes+reports retainidentity.

IMPORTANT nativearchive CHANGED after backup/hashguard:
physics/cpp/build-ue/raftsim_water.lib now
fd988c73f10f2f1423b421fc3b6e78928d9124acba789e9fae05b75f1a51a35c.
Timer-free ordinaryRelease, noIPO. Previousd91b779b...backup exact
tmp/native-archive-before-primitives-20260907.lib. Do not assume oldarchive.
Enginebuild72968exit0,167actions940.11s, existingD6 dampingfloatwarnings.
MapSHA81f31bec...unchanged. No graphical asset edits.

Actual no-record/no-readback perf37515exit0
survey_performance_native_primitives.json, same1280x72087%RTX3060Laptop
Developmentoffscreen5+20allpriorflagsincludingactivity. Mean13.326028,
p9518.996401,GPUmean6.919853,solver8.084569ms,zero33mswallhitches,
detailbacklog.000976s. Previous14.317660/19.435900/9.000088. Bothoriginal
16.667frame/1.6solver gatesFAIL. Modest improvement, not releasequalification.

Broadengine80903exit0BUT25tests:22clean+2warning-success+1FAIL.
Reportengine-native-primitives. All14detail+2spray+5replays+guidanceunit pass.
Groundcontact20/20,2400substeps; NaturalDrift_20260908_054237 originalmap
outlet99.196755s,clearance40.133724cm,missing0,finite. Bothmaptests warnings,
NOTregisteredXY traversal. Guided fails BEFOREdriving: defaultoldflowfollowing
route incompatible with currentdepthlimitedmap. Updated default only in
RaftSimSouthForkNaturalDriftTest.cpp to guided-route-depth-limited.json.
Allprovenanceandnumerical gatespreserved; explicitoverridesstillchecked.
Build23675exit0; targeted78792exit0BUT actualguidedFAILrouteerror9.938391m
vs5m. Reportengine-guided-default-route; raw
SouthForkGuidedTraversal_20260908_055031:outlet92.641513s,clearance38.043481cm,
finite,missing0. Defaultguidance has coordinated/attainableflagsOFF, not same
as priorattainablereview. Do not blame cachephysics fordifferentguidance mode.
Bothnewfailures appended via summarize_south_fork_guided_review.py; ledger24
runs (formerly22), no repeated-until-pass. No startup-failure asphysicalpass.

Next: nativeflux/reconstruction remainCPUdominant; more work needed tohit1.6ms,
withoutreducingphysicsresolution orfreezingflow. Real boiling/crestfoam and
surfacecoupledspray stillmissing; activitydetailoptin unchanged. RegisteredXY
mapguidedtraversal stillNOTdone; ordinaryguideddefault nowruns but failsroute.
Geographicidentity/rockshape/support/fullorderedqueue remain open. Avoid
unnecessarynativearchive rebuilds (hashpublicdefine dirties167UEactions).

## Continuation: current-aware default driver and first registered-rock traversal

Previous turn progress(nativeoptimization). This turn progress: fixed testdriver
defaults and completed the previously missing first full registered-XY gameplay
traversal with provenance, sampledterrain and currentwatercarrier checks. Full
goal ACTIVE; no geography/visual/fullscene acceptance, later-riverstart orcommit.
All owned engine/build/search processes terminal. No agents/skills/researchweb.
See registered-traversal.md; data/screens registered-traversal/.

Diagnosed olddefaultfailure9.938m fromraw055031/log: peak at t60.52,station59.36,
lateral11.80; headingerror>100deg duringturn while withholding guide sweep.
Existing testdriver's coordinated/attainableexperiments nowDEFAULT for guided
tests. Normal game catch-timed APIs unchanged; NO playercontrol, thrust, yaw,
velocity,physics/field edits. Explicit RaftSimSurveyLegacyGuidanceReview restores
olddriver; oldCoordinatedSteering/AttainableTrack flags can enable independently
withlegacyflag. 4modeunitchecks addedtoAttainableGuidance existing tests.
Build19250exit0. Run12603exit0:unitclean+oldermapguidedwarning-success,
engine-guided-coordinated-default. RawSouthForkGuidedTraversal_20260908_060345:
outlet62.751862s,error3.921313m,clearance30.640734cm,missing0. Singleboundedpass,
NOTbroadrobustness orruntimechangefromcache. Priorfailuresretained.

Existing plan_south_fork_guided_review.py ran against CURRENTregisteredfields,
hashverified; newguided-route-registered-rock.json173points(-60,-9)→(112,20),
4.7x2.4m downstreamalignedenvelope, minrequired.55m,actualminimum.6310278m,
2.2m/s attainablecurrentcost. sourcegeometry4b0dfeac...a50, depthddde98cb...ad,
source_bed_sampling registered_triangles. NOTrealnavigationline/measuredbed.

Added RaftSim.Survey.SouthForkRegisteredRockGuidedTraversal, reuses observer
with explicitregisteredmode. Opensregisteredmap, exactregisteredmeshassetpath,
routefield/depth/geometryhashchecks unchanged. Missingmeshrejects. Reports now
recordmap_name,ground_mesh,registered_rock_map_review. Buildexit0 (exec791done).
Run95762exit0,engine-registered-rock-guided:1WARNING-SUCCESS, nofail. Allprior
breaking/lit/detail/finecrest/secondorder/ballisticspray/unifiedoptics/activity
flags+stationcaptures. RawSouthForkGuidedTraversal_20260908_061133:
outlet64.428728s, routeerror3.801742m,clearance33.816455cm,missing0,finite,
onecarrier/sharedscale=true,8maxbreakingsites,litparameters=true.
MapUEDPIE_0_SouthForkRegisteredRockPlayable; groundexactregisteredmesh.
Nativearchivefd988c73...a35c unchanged;map81f31bec...ad7 unchanged.

13stationcaptures; requested1280x720butactualPIE954x468, NOTperfmeasurement.
Inspected003/004/005 atstations-14.88/.02/15.05: broadwhiteSMOOTHsheets,
angularrocks/banks, notphotoreal. Copiedunmodifiedapproach/crux/runoutPNG and
rawregistered/oldermapreportsinto registered-traversal/. No newvideoorperfclaim.
Ledger expandedvia summarize_south_fork_guided_review.py to26runs; supports
explicitnewtestpath with engine_test_path perrecord, retainsallfailures and
repeated_robust_navigation_accepted=false. No repeated-until-pass.

Warning r.MotionVectorSimulation renderthreadread. NotprojectCPP. Read-only
engine source search25089finished: registration ordinaryFAutoConsoleVariableRef
Engine/Source/Runtime/Engine/Private/Rendering/MotionVectorSimulation.cpp:9;
TSRGetIntread Runtime/Renderer/Private/PostProcess/TemporalSuperResolution.cpp:1884.
Warningoriginidentified; NOmeasuredwaterinstabilitycausality, engineedits or
flag-suppression. Needtrackreleaseissuebutnotablockertowaterwork.

Nextpriority actualrealistic3Dfoam/spray/surface (screensstillclearlysmooth),
CPUflux/reconstruction8msvs1.6ms, geographicidentity/rockshape. RegisteredXY
traversal now hasONEboundedpass, notzero and not broadacceptance. Sixsampled
tubeprobesnotcontinuoussweephullproof. Avoidrepeatingcompletedoriginal-map
driverdiagnosis/currentcoverageaudits/cooks. Fullorderedqueue remains open.

## Continuation: bounded stateful secondary water, 2026-09-08

Progress turn; full goal remains ACTIVE. All owned build/engine/analysis processes
terminal. No agents. Used primary SideFX Whitewater Solver HTML as architecture
reference (not Houdini integration or photographic evidence); no skills required.
See secondary-water-review.md for detailed limitations and retained failure.

New opt-in `-RaftSimSecondaryWaterReview`, registered map only, requires shared
StatefulCrestReview. Does not change production assets/defaults. New public
RaftSimSecondaryWater.h pure kernel + SecondaryWaterComponent.{h,cpp}, small
VfxActor integration. 128 persistent world-space particles, fixed60Hz max4steps
perframe, retained remainder, interpolated render, 80 attemptedbirths/s total
thinned by existing source intensity/persistence, ≤6 existing sites. Birth
inherits sampled horizontal current + AUTHORed 1.2–2.8m/s up / ±.35cross-flow.
Gravity9.80665 exactairtrajectory; return to SAME CPUcontinuousmacrocarrier turns
fragment into .8s shrinking current-advectedfoam, absolute3s lifetime, dry/missing
samplesremove. NoGPUrippleheightreadback, solidsweep, volume/momentumfeedback,
vertical-liquidvelocity, repulsion or realfoamaggregate. Replaces three rapid
Niagara populations only when component ready. Other contact VFX unchanged.

Render closed engine spheres radius2–4.5cm, no sheet, no cast shadows, opaque
DefaultLit. Newmaterial M_SecondaryWaterReview in SouthForkSurveyCandidate,
SHA4b871069ce025255b755ff1a0c9e982e13b643b3041f54bf591f68ed1a5a4ea6.
Python create_secondary_water_review_material.py refusesoverwrite; creation15782
exit0/reportsecondary-water-material.json. Existingmap/native/optics unchanged.

Build72095exit0, build36113exit0. Engine15100exit0:17clean tests in
engine-secondary-water/. First scene43829 FAILEDexit1 before capture:
SecondaryWaterMotion.log, ISM assertion InstancedStaticMesh.cpp4378 at newcomponent
line137: no PerInstancePrevTransform storage. Retain evidence, no video claimed.
Fixed InitializeInstanceHistory by SetHasPerInstancePrevTransforms(true) BEFORE
AddInstances. Newengine fixture invokesexactinitializer, testsfirstexplicitbatch
andlastprev/currentdistinct. Build72507exit0. Run62204exit0:18clean successful
tests (2newparticle/history +2existingcarrier/map +14GPUdetail) in
engine-secondary-water-history/. Purekernel tests current/gravity/birthlatched/
partitionair/slope-return/dry/capacity/expiry. No fullreleaseclean claim.

Corrected capture25953exit0, allpreviousreviewflags+newflag. SAME1280x720
river_station_side focusstation8/lateral0. Actualvideo
unreal/Saved/VideoCaptures/RaftSim_20260908-000406.mp4,696sourceframes23.837s,
715decodedframes. analyze_detail_motion.analyze('SecondaryWaterHistoryMotion')
exit0, reports+1/8/16/23s PNGunder detail-motion/. Inspected8/23s: sparsewhite
flecks replacepuffyspray; MAINfoamfaceSTILLsmooth andterrainangular. NOTrealism
acceptance. 35.002s runtime spawned712 returned683 rejected16 expired670 alive26,
remainder.001952s,componentCPUmean.4382ms. Return istransitionnotdeathcounter.

Separate63964exit0 performance, no record/readback, same5s+20s protocol/RTX3060
Laptop1280x72087%,Developmentoffscreen. survey_performance_secondary_water.json:
meanframe13.87842178ms,p9519.35169983,GPUmean6.86865664,solvermean8.06794071,
zero33mswallhitches. ComponentCPUmean.3902ms att20;26alive,remainder.003904s.
Previousnative-reusebaseline13.3260/18.9964/8.0846. Single observationeach, no
statisticalattribution. Both original16.667p95 and1.6mssolver gates FAIL; no
releasequalification. ExistingexperimentalenginePythonstartupfailuresstillpresent.

Nativearchivefd988c73...a35c andregisteredmap81f31bec...ad7 verifiedunchanged.
Trackedscopeddiffcheckclean (lineendingwarningsonly), no commits/deletions.
Do not promote or increase particle count just becausekernelpasses. Persistent
fragment lifecycle nowexists asboundedexperiment, but missingdeformingBULK
whitewater isnotfixed. Nextwork must address bulkcrest/surface dynamics and
fineGPUcarrier coupling, plus geographicidentity/rockshape and performance.
Registeredmap hasONEfullguidedpass frompriorturn; no newtraversalthisturn.
Colorado/Pacuare/Futaleufu andallscene/crew/cleanup/releasequeue stillopen.

## Continuation: fine spatial detail and liquid-template inspection, 2026-09-08

Full goal ACTIVE; no completion/promotion. See fine-detail-review.md. Added
opt-in RaftSimFineDetailReview (requires StatefulCrestReview), 256²/0.25 m grid
and level-3/0.1875 m conforming mesh, same 64 m domain and unchanged forcing.
Upsamples the complete original flow/source field; not new hydraulic data.
Snapshot reader and material ownership masks now handle actual grid cell size.
Fine material SHA06a881df1695ba918444a1e64d6b63012f4e606c074f4e319d02d11699d98054.
Creation95892exit1 transient pin warnings retained; fresh audit46186exit0.
Build12487exit0; tests56256exit0, engine-fine-detail/:19 clean successes.
New FineSpatialWaveGPU RMS .00893975903→.00214706354 m at fixed physics/time step.
Capture5075exit0: RaftSim_20260908-004029.mp4, FineDetailMotion reports/frames.
Inspected8/23s still smooth foam/angular terrain. Fine live GPU foam-cell RMS
11–15 mm, not bulk breaking water. SecondaryWaterReview off for this comparison.
Perf43836exit0: fine_detail JSON, mean13.287/p9518.795/GPU7.632/solver7.965 ms,
one >33ms hitch; original gates FAIL. Map/native/project/original optics unchanged.

New read-only RaftSim.InspectLiquidTemplates <json> command in editor module.
Requires process-only -EnablePlugins=NiagaraFluids. Build52533exit0 after fixing
UE_LOG macro else braces. liquid-template-inspection.json shows current Windows
Splash/Hose/Pool/Coupled ready, GPU stages and SDF/screen-space renderer assets.
Does NOT prove selected mode/particle visibility/rendered liquid. Historical V9
Mac direct-template failure remains valid. Next inspect render mode/bindings;
only project-owned explicit renderer/coupling could address that earlier failure.
Inspector1306 saved report but ignored queued Quit. Verified owned PID36328
explicitly closed, terminalexit1. All owned processes terminal at checkpoint.
No agents, no commit, full queue open. Do not repeat fine-grid experiments as
substitute for deforming bulk liquid or geographic identity/geometry work.

### Renderer inspection follow-up (all owned processes terminal)

Read fine-detail-review.md renderer follow-up. Native inspector now records
renderer bindings, all embedded graph pins, static rapid-iteration values, and
shared FLUID_CONTROLS module. Report liquid-template-bindings.json ~7 MB, contains
old graph versions too; filter paths before interpreting. UseScreenSpaceRendering,
UseMeshRendering, UseDirectSDFRendering gate respective renderers. Shared module
StaticSwitch selector comes from Module.Rendering Method; enum path
/NiagaraFluids/Enums/ENiagaraFLIPRenderingMethod. Its switch node is
...Grid3D_FLIP_FLUID_CONTROLS:NiagaraScriptSource_2.NiagaraGraph_0.NiagaraNodeStaticSwitch_0,
InputParameterName undefined (exposed selector pin, NOT named staticparameter).
MapGet_6 has anonymous input default NewEnumerator0, but its corresponding output
and selected compiled version are not yet verified. Do not call SDF selected.
Hose GPU rapid-iteration external-collision switches are all0.

Read-only wrapper unreal/Scripts/inspect_liquid_templates.py runs command and
explicit quit_editor, fixing first lingering process. Build73897exit0 with
deprecated bool overload warning; replaced with EGetObjectsFlags. Build97133,
85174,26778 exit0 clean. Runs47878exit0,19454exit1,24922exit1, final36431exit0.
Logs LiquidTemplateBindings/BindingsFull/Controls/Selector respectively. Saved
reports are not rendered-fluid evidence. Python private-property read attempts
55665/36258 both process0 but scriptErrors; logs LiquidRenderSwitch and
LiquidRenderSwitchData retained. Failed short helper removed; native reflection
works. Final code built; no system spawned, no asset saved, no new scene capture.
Next useful action is an explicitly selected project-owned renderer in a bounded
isolated liquid fixture, prove moving bulk liquid and measure cost before river
terrain/current coupling. Do not repeat anonymous enabled/active checks as proof.

### Explicit liquid fixture (all owned processes terminal)

Read liquid-body-fixture-review.md. Project-owned NS_LiquidBodySDFReview created
with explicit Direct SDF enum NewEnumerator0 overrides in two copied graph
versions, exactly one renderer and owned copied SDF MIC. Asset SHA
f193332042962d24beccc04f338664cf4d2b1b0e97dff931b9e5b7f7332108a5.
Hose-derived 4x4x5 m, max-axis64, four particles/cell, pressure40. No river
coupling, no production scene change, no physics or photorealism acceptance.

Factory command RaftSim.CreateLiquidFixture refuses overwrite. Editor now has
private NiagaraEditor dependency; plugin mounted only by process flag. First
build65812 failed unexported graph NotifyGraphNeedsRecompile; corrected exported
MarkNodeRequiresSynchronization. Builds15540/67246 and creation46279 exit0.
Ownership test46264 exit0, engine-liquid-fixture one clean success.

Capture harness MUST use -ExecCmds=py ABS_SCRIPT, not ExecutePythonScript.
Wait for component is_active before disabling normal tick. CPU age alone did
not establish GPU execution: first profile (Angles) had no Niagara compute.
Final Viewport run61734 enables/invalidate normal editor viewport each frame;
CaptureLiquidFixtureViewport.log records real FLIP/pressure/rasterization.
liquid-body-sdf-viewport has 4/5/6s views, frozen side/low views, hidden control.
Actual ages3.999997/5.000010/6.000023. Analyze script records pixel deltas, not
animation acceptance. Inspected volume/jet is 3D but too dark, not whitewater.
One whole editor GPU frame16.31ms, Niagara compute4.050ms inclusive,
FillRasterizationGrid2.293ms,40 pressure iterations. Particle dispatch286455
is not live particle count. Earlier failed/ambiguous captures retained.
Project descriptor, registered map and native archive unchanged. No commit.
Next establish explicit current/stage boundaries and terrain collision, improve
optics and profile surface cost. Never overlay the toy cube on the river.

### Liquid primitive collision follow-up (all processes terminal)

Read appended tagged-obstacle section of liquid-body-fixture-review.md.
CreateLiquidFixture optional collision creates distinctNS_LiquidBodyCollisionReview
SHA6fdf53c11508e37fdde6ad7bcea46490b3140e57843c9bd5a13ec92b58f5d99b.
Two boundary graph versions explicitly MeshCollisions=true, MeshDF=false;
owned rigid-mesh interface tagRaftSimLiquidFixtureObstacle,static allowed,
simple geometry,max16. No engine or existing fixture edits.

Native LiquidFixtureParticles <json> snapshots actualGPU through an allocated
sim cache. Initialnullcachefailure retained, corrected. No DI caching, so
engine warns missingmaterialSimRT forcacheplayback; not a playback test.
Actualtankzstarts0! Oldspherez-60 only touched bottom and was not useful.
Corrected spherecentre(0,0,100)radius80;floorvisualtop0. Capture script optional
Collision or ObstacleControl plusReadback. Latest outputs
liquid-body-obstacle-in-water and liquid-body-obstacle-control. Three4/5/6s
samples allfinitepositions, core60cm counts enabled0 vs disabled9472/9686/9615;
maxsurfacepenetration4.46/3.91/3.76cm (within7.8125cmcell,NOTexactexclusion).
Comparison scriptanalyze_liquid_obstacle.py exit0,liquid-obstacle-comparison.json.
Main/lowcapturesstilldark bounded blue tank/jet,not realisticwhitewater.

Builds51483/82235/88873/66777 exit0. Creation87990exit0. Render50839exit0
oldsphere. Readback61373process0 butscriptfailednullcache;78908exit0oldsphere.
Enabled41791/control83343 completecorrectedsphere; no viewportensure after
scriptfalse-then-trueoverridefix (true removes namedoverride; doesn't add it).
Finaltest62555exit0, engine-liquid-collision2cleansuccesses. Originalfixture,
registeredmap and projectdescriptor hashes unchanged. No commit/production.
Next explicit river inlet/outlet/stage, captured bed collision, single surface
ownership and raftsupport. Primitive response is now proved; don't repeat the
same sphere experiment as a substitute for actual river coupling and optics.

### Standalone channel follow-up (September 8; not river acceptance)

The inherited Hose emitter restored closed boundaries on reload/compile even
after graph overrides and removal of eight stale rapid-iteration values.
Source bindings compiled correctly, but the inherited source also kills new
particles inside existing negative SDF. A dry start removes that inlet conflict.
Latest NS_LiquidChannelOwnedReview detaches emitter parents before editing;
runtime +X outflow now works. Four user inlet controls and User.Open Outlet
are linked, with regular and high-precision outlet paths. Saved standalone
has two outlet links, not four duplicate parent/current graph references.
Initial configuration report engine-liquid-channel has two successes and one
failure for that wrong count; retain it. Correct test must check both paths.

liquid-channel-owned-stop is actual GPU readback at 4/5/6 seconds. At4s there
are21733 particles, zero nonfinite positions/velocities and zero in radius60cm
obstacle core. Downstream meanVx251.35cm/s includes escaped particles, so it
is NOT in-domain discharge. After inlet stops at4s,21669 remain at6s and
minZ=-13446.55cm: escaped particles are not retired and fall indefinitely.
The dark-blue shallow fixture is not realistic whitewater or river integration.
Next implement bounded outflow retirement and in-domain accounting, then
stage/current coupling, captured terrain, single surface and raft support.

Latest asset SHA256 bfa7f5d85fe4c9ee8d173cd9438a2fdfd990120b9fd19e8cbdc1f8d3d6d6de56.
Retained predecessor assets ChannelReview, FlowReview, BoundaryReview and
OutletReview failed to establish outflow; do not repeat those inherited tests.
Shader inspection console currently targets OutletReview, not OwnedReview.
Initial liquid-channel-shaders dumps were empty; force-compile dumps contain
three translations. Inspection41880/37867 and creation87384 exited1 despite
normal-looking shutdown and outputs; not clean successes. Last build67759,
creation22120,capture43060 exited0. No current-channel performance measurement.
No production promotion, commit or goal completion. Entire queue remains open.

### Bounded channel retirement (all processes terminal)

NS_LiquidChannelBoundedReview now retires particles outside the fixed 4x4x5m
domain using KillParticlesInVolume (Box, Invert=true, enabled, origin offset
0/0/250cm). Appended at particle update; the later FLIP integration can cross
the outlet for one final timestep. Runtime four/five/six-second GPU readbacks
in liquid-channel-bounded-stop: counts13878/10620/7903, outlet pending55/41/21,
maximum overshoot3.995/4.099/3.358cm. Zero belowfloor, nonfinite or spherecore60.
Current regions now exclude off-grid particles. Actual in-domain downstream
meanVx189.26/182.01/147.21cm/s. Analyze_liquid_channel.py passes and records
43.05% count reduction in two seconds after stopping inlet. Not mass calibration.
All-axis retirement is a lifecycle guard, not face-resolved flux accounting.

AssetSHA11da793eeb4e905a3bd9b45c85d5464ad95b6051c6302af209d457420ad268cd.
Factory/capture optionalflag-RaftSimLiquidFixtureBounded selects it; original
Channel flag still selects Owned. No assets overwritten. Inspection output
liquid-retirement-inputs.json includes KillParticlesInVolume graph inputs.
Read body review for full failures. Creation28979exit1 despite saved=1;
fresh capture91037exit0 and complete. Actual image inspected: darkblue shallow
liquid aroundsphere, NOT photorealism. Equal PNGsizes don'tmeanfrozen;
hashes differ (early commentary suspicion was corrected). No renderer regression.
Build7047failed nonexportedFindOutputNode, nextfailed TObjectPtr deduction;
fixed by iterating graph Nodes/Cast/GetUsage. Builds44268/67128/40938exit0.
Firstsuite52685 threepass/onefail because SuggestedName is not FunctionName.
Fixedtestresolvesactualscript thenalias. Final53416exit0; report
engine-liquid-bounded-alias has4cleansuccesses,0warnings/failures,6.59seconds.
OriginalOwnedtestnowassertsexactly2 distinct outlet bindings, bothpass.
Analyzeranddiffcheckexit0. Descriptor and registeredmap hashes unchanged.

Next advance to calibrated inlet/stage and measured flux/captured terrain
coupling, optics and performance. Do not repeat this sphere/retirement test as
river progress. Existing fixture remains isolated, no production promotion or
commit, appgoalACTIVE and complete queue unchanged.

### Captured crux solid and native face-flux handoff (September 8)

Read liquid-terrain-coupling.md. Prior turn classified progress; this turn also
makes authoritative changes. All owned sessions are terminal. No subagents.
New physics/scripts/build_south_fork_liquid_window.py clips exact registered
triangles into a closed24m patch, preserving201rockreturns atstation/lateral0.
NewSourceArtSouthForkLiquidWindow20260908 has6334closed/5032toptriangles.
Top independent centroid maxerror7.9048e-14m. Initialwrongbottomwindingfailed
beforewrite; corrected. Sixunittesttests pass; pytestunavailable, notinstalled.
Export viaBlender5.2 succeeded. Import8394exit0 verifiesall5032toprayprobes at
realtransform(yaw158.434789deg,origin0/0/350cm),maxerror.00120595cm. Newasset
/Game/RaftSim/Environment/SouthForkLiquidWindow20260908/SM_SouthForkLiquidCollisionSolid
SHA1ce164f5de059d7bf08373b65168cfac45d7f1feb3bf41cb3e8259de4a0dff79.
No level saved. Import has UV/tangent/smoothing anddeprecatedquerywarnings;
fixbeforevisualuse. Build54029exit0,engine87361exit0,engine-liquid-terrain has
5cleanpasses,6.57s. ActualSDFvalid37³indirection19136bricks455072residentbytes,
notMostlyTwoSided. GPU terrain separation NOT proved; don't infer it fromraytests.

First20m boundaryprofile has2dry/nonzeroQconflicts,notready. Do not feed it to
FLIP or silentlydeleteflux. Native solver nowexportsall MUSCLnumericalmassfaces
usinginspect_numerical_mass_flux_grid()/--inspect-face-fluxes; no mutation,
dt0scratch, noallocnormalstepping. Added nativeuniform/boundaryidentity checks.
SeparateVSReleasebuildtmp/south-fork-liquid-flux-build-20260908;build72739exit0,
all3CTestfixturespass. Oldcookbinaries andengine-linkedarchive NOT replaced.
NewexeSHA0cd6cefbe75173e74dab8266d3230764cc5cfd6d9a614fe847001131f15bf153.
Audit_south_fork_liquid_flux.py verifiesfinalscenarioendpoint againstengine
h/u/v/bedarrays, exportsactualfluxgrid, runs1usstep. Actual21mcontrolvolume
faces±10.5m:netQ.0311408647374,measuredstorage.03113951508m3/s,error1.35e-6
passes1e-3gate. Do notcomparethisdifferentboxdirectlytothe20minterpolatedbox.
Report/arrays/tinystep inliquid-native-face-flux. No 3Dcoupling or sceneacceptance.

Next: consume exact native faces in a grid-aligned21mcrux handoff, resolve
fine-bed partial wet support conservatively, terrainSDFparticletest, single
surface/raftsupport/optics/performance. Preserveinferredbed/unverifiedrapid
identity labels. No productionpromotion/commit/goalcompletion. Avoid another
isolatedsphere/tank experiment; actualcapturedterrain andflowhandoffnowexist.

### Native wet-source arrays and actual captured-terrain GPU coupling

Read liquid-terrain-sources.md before resuming. All owned sessions terminal;
no agents. Source builder emits4496 weighted position/velocity samples, preserves
nativeQ46.779617074m3/s to8.88e-16 error, minimum clearance0.270mm underresolved.
New isolated asset NS_SouthForkLiquidTerrainReview saved84674exit0, SHA49be4cc3...
full identity in review. Factory uses reflected weighted alias DI plus vector
arrays, one per-particle index shared by position/velocity, actual connected
spawn-stack culls disabled, exactterrainDF enabled, four lateral facesopen.
First34307 found3culls/refusedsave; fixed parameter-map walk (not nonexported
GetOrderedModuleNodes). Wrapper now asserts physicalfile too.
Source helper widthvalidation and8unittests pass. Builds71168/66964/17710exit0.
Engine89124exit0 engine-liquid-terrain-sources has6cleanpasses,7.16s.

New capture_south_fork_liquid_terrain.py loadsregisteredmap WITHOUTsaving,
hideslegacywater, exactsolid at0/0/350 yaw158.434789, excludes collider from
main/depthrender butkeepsDFregistered. Usesmanual1/60GPU, reads at4/8/12s.
Readback now localdomain + exacttrianglebed rayprobes, requiresoneProbeactor.
First42462tiltedterrain due positionalRotator, invalid. Keywordyawfixed,
forward/up guardsadded. Correct68962exit0: finiteparticles/domaincontained,
counts2599/2599/2601; belowonecell2/4/1; maxpenetration168.52/160.84/35.76cm.
Control25404exit0 has1261/1285/1248deepbedparticles. Couplingproved, NOTcorrect
separation/mass/visuals. Lowretention mostlyinlet needsactualmassaccounting.
Lit42454exit0 andshader72573exit0. Currentharness addsunsavedlightoverrideand
exposurebracket; originalsun3lux. Darkfirstcaptures/overexposedlitones; bracket
imagesinspected showgiantblueverticalsheet, NOTwhitewateracceptance.
Actualcompiledshader inliquid-terrain-shader-runtime/compiled_shaders confirms
matchedweightedindex andretirement butremainingSimStage13KillParticles uses
roundedsolidcellmask; candidate sourceofloss, notyetquantified. Don'tdisable
collisionormasslossgates. DumpLiquidChannelShaders acceptsoptionalterrain.
Map/descriptorhashesunchanged; scopedgitdiffcheckpass; nopromotion/commit.
Next accountbirth/loss/outflow, terrainseparation, stage, SDFtransformandmotion,
thenraftsupport/optics/performance; goalACTIVE, fullqueueunfinished.

### Actual particle identities isolate solid-cell deletion

Read liquid-terrain-loss.md. Previousgoalturn=progress. Currentnewbaseline
liquid-terrain-particle-identity (41350exit0), build84927exit0 exports actual
GPU UniqueID/RiverSourceIndex/localpos/velocity rows plus systemtransforms/dt.
At12s2592particles ID223311..227310, medianapproxage.26s oldest.76s, nominal
rateadvancing. Actualdt1/60, UnitToWorld21x21x8m yaw158.4348 centre0/0/750,
bottom350, correct. StartupIDsbegin163840 (inheritedtankburstalloc stillthere).
Do notclaiminitialwatermasscalibrated. Allparticlesource/renderassetsunchanged.

NewconsoleRaftSim.LiquidTerrainSolidLossControl transientduplicateonly disables
activefluidgraph KillParticles driven bysolidcellmask. Firstbuild40498/control
59818 matched2nodesandrefused; capturecontinuedasbaseline. INVALIDcontrolfolder
liquid-terrain-solid-loss-control retained. Fixedactualfluidgraphfilter;
Python nowassertsassetcontrolinstalled. Build27675exit0; control25896exit0 in
liquid-terrain-solid-loss-active-graph. Counts440/2555/5186/21001/42079/63160 at
.1/.5/1/4/8/12s vsbaseline439/2140/2590/2599/2613/2592. At12s49510belowbed1mm,
350belowonecell,max231.08cm,0outside. Soliddeletiondominantloss CONFIRMED;
removingitisNOTfix/acceptance. Needprojectcontactoutofbed+tangentialvelocity,
keepterrainpressure andescape; propercapturedwetinitialstate insteadoftank.
Engineheaders inspected: meshDIGetClosestPointMeshDistanceFieldAccurate returns
distance,position,normal,velocity,normalvalid,maxencoded; supportsGPUonly.
StockCollision/NiagaraDistanceFieldCollisions modules exist; notyetinspected.
CustomHLSLSetCustomHlsl/InitAsCustomHlslDynamicInput andRequestNewTypedPin not
exported; ReallocatePins exported, CustomHlsl propertyreflectededitable.
AvoidanothernonexportedAPIlinkerexperiment; preferexistingcollisionmodule.

Lightingharness now1xambient(not1000) andunsavedexplicitdownward50kluxsun.
Actualbaseline/controlhighangleimagesinspected: angularterrain,no convincing
liquid. NeedruntimeSDFmaterialbounds/cameraclearance, notopticsacceptance.
Savedterrainasset49be4cc3... registeredmap81f31bec... descriptor01b95fff...
rehashesunchanged. No promotion/commit, fullgoalACTIVE. Regression29224exit0,
engine-liquid-terrain-identity has6cleanpasses,7.31s; scopedgitdiffcheckpass.
Allownedsessionsnowterminal. No processneedswaiting. Continueactualcontactfix.

### Non-deleting contact implemented; flow-through still fails

Read liquid-terrain-contact.md. Current goal turn made implementation progress;
not blocked and not complete. New source RaftSimEditorLiquidTerrainContact.cpp
creates NS_SouthForkLiquidTerrainContactReview from baseline. It disables actual
solid KillParticles and appends stock GPU distance-field Collision after FLIP
particle update in simulation stage13. Explicit Custom2cm radius, correction,
no killing/rest/bounce/friction. Pressure/source arrays/escape retirement remain.
Stock FLIP update STILL zeros velocity in solid-classified cells before contact;
global DF response is not the exact tagged mesh query. Need tangential momentum,
captured wet-volume initialization and flow/mass validation next.

First asset66f8fde0... run39611 at12s63048live,2517belowbed1mm,124belowcell,
max59.0295cm. Radius update first failed saved0; wrapper detected unchangedbytes.
Retain CaptureLiquidTerrainContactRadius as UNCHANGED first asset evidence.
Loaded-package update67739 succeeded(saved1). Corrected current asset fullSHA
eefde2513997e3cfa1206acc1bc053b6a3729280cfa7c5eae9df6230dc714122.
Original backup tmp/liquid-terrain-contact-before-radius-20260908.uasset.
Corrected capture57819 liquid-terrain-contact-opacity-runtime at12s63075live,
2466belowbed1mm,133belowcell,max59.0295cm,0outside,mean52.32cm/s. Baseline
deletion2592live vs bypass63160live/49510belowbed: retention improved, physics
still FAILED, particle volume uncalibrated. No production promotion or commit.

Runtime material/bounds exported by LiquidFixtureParticles. Material centre750cm,
WorldGridExtents2100/2100/800, voxel16.40625, yaw158.4348; Opacity0,Absorption.a
.056,Scattering.a.0001. Runtime-only LiquidTerrainOpacityReview command changes
MID only. Initial high-view opacity comparison terrain-dominated. Moving camera
after freezing leaves camera-facing carrier stale; do NOT treat multi-angle
camera-isolation4284 as proof of missing geometry. First overhead94055 also
FAILED atHiddenActors editorproperty. Supported hide_actor_components works and
is camera-only, leaving global DF/collision unchanged.

New -RaftSimLiquidTerrainFixedOverhead starts camera(0,-1,35)localm looking(0,0,3)
before activation, holds throughout. Fixed overhead76689 completed butwaternear
black. Following fixed-opacity73596 completed: liquid-terrain-contact-fixed-opacity
fixed_overhead_opacity_one and fixed_overhead_water_only inspected, show a narrow
blue/white inlet strip. Readback verifiesOpacity1. Surface exists butmostlyinlet
accumulation: othercorrectedrun56250/63074upstream,centreVx10.19,downstream-11.90
cm/s. No broadwaterface, realrapids, contactacceptance or opticsacceptance.
Harness nowfixedmode at720originalcapture,724opacity1readback+hideterrain,
728wateronlyreadback+hideliquid,732emptycontrol+finish. No savedmaterialchanges.

New RaftSimEditorLiquidTerrainContactTest.cpp checks savedready, actualfluidgraph
nodeenabledstates, 1contact/disabledsolidreject/enabledescape, Customradius/DF,
noKill/noBounce/noFriction, unchanged4496sourcepositions/velocities,1renderer.
Build83460 failed unexported GetModuleIsEnabled; fixed inline public nodeaccessor,
build77342exit0. Test63508exit0: engine-liquid-terrain-contact/index.json7clean
passes0warnings0failures7.74s. These are configuration, not simulation acceptance.
Map81f31bec...,descriptor01b95fff...,baseline49be4cc3... unchanged;scopeddiffcheck
pass. All owned builds/captures/tests terminal. Full queue goal stays ACTIVE.

### Coarse-cell motion preservation tested and rejected

Read liquid-terrain-momentum.md. Prior turn=progress; current turn=implementation
and causal GPU evidence, not blocked/completed. Engine graph inspection added
Grid3D_FLIP_ParticleUpdate; inspect_liquid_contact.py nowwrites
liquid-particle-update-inputs.json, build51671/inspection59603 exit0.
Solid select truepins Position=oldPosition,Velocity=zero. Outer select truepins
are oldPosition+Velocity*dt and oldVelocity. New console
RaftSim.LiquidTerrainMomentumReview in RaftSimEditorLiquidTerrainContact.cpp
transientduplicates contact system and owns functionscript; rewires only solid
truepins to outer inertial branches in2copiedgraphs. Non-solidFLIP/PIC,pressure,
sources,escape and existingglobalDFcontact preserved. No persistent writes.

Build84133exit0, firstcapture77636 installed2selectors butharnessfailedframe6:
readbackfilterrequiresLiquidBodyReview inassetpath. Retain
liquid-terrain-momentum-runtime as INCOMPLETE, notphysicsevidence.
Transientname nowSouthForkLiquidTerrainMomentumReview_LiquidBodyReview; build4787
exit0. Validcapture37669exit0 inliquid-terrain-momentum-readback.
Use -RaftSimLiquidTerrainContact -RaftSimLiquidTerrainMomentum
-RaftSimLiquidTerrainFixedOverhead withunique label. Harnessassertsinstalled.
At12s59222live,399belowbed1mm,356belowcell,max307.03cm,8outside. Priorcontact
63075live,2466small,133deep,max59.03cm. Motion preserves moremotion but WORSE
deepseparation. REJECT asfix. 54651upstream,meanVx12.86upstream/-159.97centre/
-85.05downstream. Opacity1fixedoverheadimageinspected: sameinletstrip, notriver.
No calibrated mass, no performanceacceptance, no promotion/commit.

Regression18326exit0 engine-liquid-terrain-momentum7cleanpasses7.56s. Testsare
savedfixtureconfiguration, NOTacceptanceoftransientvariant. Scopeddiffcheckpass.
Savedcontacteefde251...unchanged. All owned sessions terminal; nothingtowait.
Next replace globalDFcontact with taggedmesh accuratequery thenvalidateactual
trianglebedseparation andtangentialvelocity; capturedwetinitialstate/mass stillopen.
EngineDI GetClosestPointMeshDistanceFieldAccurate GPUonly confirmed in
NiagaraDataInterfaceRigidMeshCollisionQuery.cpp around1803: inputs CollisionDI,
WorldPosition,dt,TimeFraction,MaxDistance; outputs ClosestDistance/Position/Normal/
Velocity,NormalIsValid,MaxEncodedDistance. No implementationyet ofprivatequery.
NiagaraNodeCustomHlsl CustomHlsl FString reflected private; Signaturepublic,
ReallocatePins exported; SetCustomHlsl/InitAsCustomHlslDynamicInput unexported.
Do not repeat linkerfailures. NiagaraNodeParameterMapGet headersPRIVATE; public
NiagaraNodeInput supportsInputvariable/Usage/ExposureOptions. Preserveengineassets.
Fullqueue goal ACTIVE, SouthFork stillincomplete, otherqueued scenesnotadvanced.

### Tagged mesh contact implemented; fluid-update instability exposed

Read liquid-terrain-private-contact.md. Prior turn=progress, current turn is
actual implementation + GPU evidence that changes next action. Goal ACTIVE,
not blocked/completed; no promotion or commit.
RaftSimEditorLiquidTerrainContact.cpp helper AddPrivateTerrainProjection builds
custom HLSL node in each owned FLIP update graph. Copies existing MapGet sooutput/
default GUID metadata is retained; changes typedoutput toUser.Collide_Meshes.
CustomHlsl reflectedFString setviaFStrProperty; Signaturepublic; publicvirtual
AllocateDefaultPins WORKS. ReallocatePins PROTECTED, AddParameter UNEXPORTED:
don'trepeatthosefailedbuilds. Correctedbuild2746exit0. Customnode queries tagged
meshDI GetClosestPointMeshDistanceFieldAccurate; globalCollisiondisabled onlyin
privatevariant. Actual Engine.DeltaTime nowinput. Entirefluidgraph ownershipmust
beIsIn(transientSystem), checkedbeforeedits. No engine/privateheadersneeded.

Console RaftSim.LiquidTerrainMomentumReview private. Captureflags
-RaftSimLiquidTerrainContact -RaftSimLiquidTerrainPrivateContact
-RaftSimLiquidTerrainFixedOverhead -RaftSimLiquidTerrainLabel=UNIQUE.
Systemtransientname includesMomentumReview_Private_LiquidBodyReview. Pythonasserts
privateinstalled. First86643 mistakenlylaunchedafterfailedbuildloadedoldmodule;
privateidentityassertstopped. INVALID liquid-terrain-private-contact-runtime.
Initialprivate2876exit0 inliquid-terrain-private-contact-readback butgraphlink
ensures. DuplicatepinLinkedTo arraysarenotreciprocal; BreakAllPinLinkscaused
ensures. NowclearONLYnewcopiedarrays withLinkedTo.Reset beforemakingnewlinks.
Build78767exit0, audit24933exit0 liquid-terrain-private-query-audit noensures.
At12s54888live,467belowcell,max479.70cm,18outside,52818validnormalqueries.
Invalidenginequerynormal isuninitialized; currentexportzeroeswheninvalid.

Trajectoryvariant stepsalongold-to-proposedposition8cm,max32substeps; up to4
projectioniterations/substep, radius2cm, correctionmax100cm/query; removesinward
velocity andinwardremainingtravel only. Invalidnegativequeryreturnspriorstep
position,no kill. Build64525exit0/run47542exit0 liquid-terrain-private-swept-contact:
52746live,977belowcell,max545.13cm,87outside. StillFAILED,nopromotion.
Currenthelperalsoexports QueryWallSpeed and StepLength. Build91558exit0 and
run87302exit0 liquid-terrain-private-wall-audit. At12s53572live,1563belowcell,
max576.03cm,9outside. ALLqueriedwallvelocities0. Meanproposedstep2.73cm butmax
3607.46cm PER1/60s;67particles exceed32x8cmsubstepbudget,3463invalidnormals.
ThusmotionofterrainRULEDOUT asvelocitysource; fluidupdate runaway confirmed,
notcuredbyprivatecontact/substeps. Correctedquery andlatestopacity1imagesinspected:
patchy inletconcentration, notfilled/realisticriver. No mass/performanceacceptance.

CurrentJSON emitters[0].private_contact_query_rows columnsstring
distance_cm,normal_valid,normal_z,wall_speed_cm_s,proposed_step_cm; alignedto
particle_rows. Older private audits had private_contact_distance_valid_normal_z
threecolumns. Finalfixturetests90429exit0 engine-liquid-terrain-private-contact
7cleanpasses7.77s; thisissavedconfigregressionNOTprivatephysicsacceptance.
ContactSHAeefde251...,map81f31bec...,descriptor01b95fff...unchanged. Scopeddiffcheck
passes; all ownedprocessesterminal. Nothingneedswaiting.

NEXT: stopminorcontacttweaks; auditactualFLIP/PICmix,timestep, pressureandparticle-
gridvelocity transfer andinletNQcrowding/sourceflux. Propercapturedwetinitialstate
andboundarystage/momentum exchange stillmissing. Native sourceprofilebuilder
physics/scripts/build_south_fork_liquid_sources.py hasvalidatedmesh+hydraulic
loaders andexactbed sampler; currentlysourceonly, nominalparticlevolumeunverified.
Compiledbaseline GPU shader28 lines6627-6629 bindsFLIPLocalToWorld=Emitter.LocalToWorld,
WorldToUnit=Emitter.WorldToUnit,PicOrFlip=Emitter.controls.PICFLIPRatio. Actualmix
notyetexported. Inspect ratherthaninfer; preserveoriginalall-sceneacceptancegates.

## September 8 — particle/grid basis defect corrected in transient candidate

Goal ACTIVE, queue incomplete, no promotion/commit. Meaningful physics progress,
not a blocked turn. Report: liquid-grid-frame-transfer.md.

Settings capture26014 completed, liquid-terrain-fluid-settings-audit. Its actual
GPU particles pile up at x=-985.7cm (two-cell inlet band); 430 below one cell,
max554.64cm penetration and proposed step4308.92cm at12s. Runtime dt1/60,
40pressure iterations; compiled PICFLIP ratio0.75. Neighbor DI uses dynamic
storage, BUT the rasterizer consumer caps CurrNQCount at MaxParticlesPerCell,
bound to Emitter.OVERRIDE.ParticlesPerCell. Earlier reasoning that ruled out all
neighbor truncation was too broad: storage and consumer differ.

CONFIRMED P2G BUG: compiled stock Grid3D_FLIP_RasterizeNQParticles averages world
particle velocities and writes them directly to local velocity grid; G2P then
rotates by grid LocalToWorld. At yaw158.4348 this is an extra rotation. Added
CorrectRotatedParticleTransfer in RaftSimEditorLiquidTerrainContact.cpp. It copies
the active function into transient system and projects worldVelocity onto
normalized UnitToWorld row axes after averaging. Both stock gather branches
corrected; use-simple-weight remains unchanged. No force or clamp added.

Command RaftSim.LiquidTerrainMomentumReview grid-frame starts private swept
contact + basis correction. complete-gather also removes initial-density clamp
from both gather branches (uses actual allocated neighbor count). Captureflags
-RaftSimLiquidTerrainGridFrame or -RaftSimLiquidTerrainCompleteGather, with
-RaftSimLiquidTerrainContact -RaftSimLiquidTerrainFixedOverhead and fresh label.
Identities include _Private_GridFrame_ and optional _CompleteGather_. New
-RaftSimLiquidTerrainDumpActiveShaders exports ACTUAL transient GPU shaders;
DumpLiquidChannelShaders now accepts active with world/unique-component check.

First9241 failed identity assertion (guard expected one HLSL node, actual2);
liquid-terrain-grid-frame-review INVALID. Two-branch guard build59403 passes.
Capture56650 exit0 liquid-terrain-grid-frame-readback:50366live, medianX-574.9cm,
12484centre particles (vs956), maxproposedstep60.08cm,21belowcell,max538.88cm,
35outside. Much better spread, still fails. Bin max840 vs3811, not actual NQ read.

Build8072 exit0; complete-gather capture37374 exit0:
liquid-terrain-complete-gather-readback.59250live, medianX-646.2cm,
7983centre, maxproposedstep71.30cm,14belowcell,max253.73cm,8outside. Binmax5222,
worse crowding. Both opacity-one overhead images inspected: large pale/smooth
patchy liquid, not realistic. Do not claim full gather universally improves.
Active shader28 lines2995+ prove normalized-basis projection and no count clamp.

New test LiquidFixtureTerrainGridFrameTransfer builds both variants, checks
actual GPU translation, transient ownership, unchanged source arrays and saved
package cleanliness. Build70857 exit0, regression23502 exit0. Report
engine-liquid-grid-frame/index.json:8cleanpasses,0warnings/failures,9.47s.
No physical/performance acceptance implied. Contact/map/descriptor hashes remain
eefde251.../81f31bec.../01b95fff...; exact hashes in liquid-grid-frame-transfer.md.
All owned captures/builds/tests terminal; no processes require polling.

NEXT: retain basis fix and implement wet hydraulic startup + actual inflow/outlet
exchange. ALSO definite boundary-name mismatch in source factory: shader
Right/Left=X, Down/Up=Y, Back/Front=Z. Factory opens Right/Left/Front/Back;
compiled Down=false although native south-side source points exist. Correct
lateral Y openness (Down/Up); don't call Front/Back horizontal lateral faces.
No such face correction implemented yet. After physical consistency, optical
SDF material and performance still need actual motion validation; original
Colorado/Pacuare/Futaleufu/all-scene/crew/cleanup/release queue unchanged.

## September 8 — wet hydraulic startup and boundary mapping implemented

Goal ACTIVE; this turn made implementation/runtime progress, not blocked.
Report liquid-wet-initialization.md. Full queue incomplete, no promotion/commit.

CorrectRiverBoundaryAxes now overrides all six controls on the one owned
Grid3D_FLIP_FLUID_CONTROLS call: Right/Left/Down/Up/Front=true,Back=false.
Removes stale rapid constants before setting override pins. Source factory
RaftSimEditorLiquidTerrainSource.cpp corrected for future generation too;
saved baseline untouched. New command argument open-sides includes complete
gather + grid-frame + private contact. Build58641 exit0, capture45737 exit0:
liquid-terrain-open-sides-readback, CaptureLiquidTerrainOpenSides.log. Shader
SystemSpawn Constant209..214 true,true,true,true,true,false confirms mapping.
12s59184live,79belowcell,max194.18cm,13outside; stillfails.

New physics/scripts/build_south_fork_liquid_initial_state.py loads verified
registered mesh + same hydraulic fields, samples128²columns at21/128m, uses
exact bed and interpolated stage/momentum/source-depth. Equal nominal particle
volume (21/64)^3/4, deterministic largest-remainder counts, interior vertical
quadrature. 77085particles, minbedclearance.0810168164m. Wetquadrature
680.8111195762m³, nominalrepresented680.8130121231m³,error.0018925469m³.
Not mass-calibrated; source 2D implies explicitlyzeroverticalvelocity.
Generated SourceArt/RaftSim/SouthForkLiquidWindow20260908/hydraulic_initial_state.json
SHA4e34428973aa0b814e875c22d2f6157b4b3db128041b5f9cfedebeb14f33580e.

InstallHydraulicInitialState in LiquidTerrainContact.cpp copies actual initializer,
replaces ONLY initial selector true inputs (position,velocity,Transient.Kill)
with ReadRegisteredWetVolume customHLSL. User initial position/velocity float3
arrays; ExecIndex/Get; reject dummyinitialindices>=77085; continuousinlet branch
unchanged. Positions are worldcm (not source offsets). Hardguard table<=163840
matches current inherited burst; not general across arbitrary scalability.
DuplicateTypedMapRead uses public cloned mapget + reflected defaultGUID mapping,
clears ONLYcopiedLinkedTo arrays to avoid graph ensures.

New command wet-start includes all corrections, nameincludes_OpenSides_WetStart_.
Capture flag -RaftSimLiquidTerrainWetStart implies precedingvariantflags; still
requires -RaftSimLiquidTerrainContact and usual unique label/fixed overhead.
Option -RaftSimLiquidTerrainDumpActiveShaders captures actualtransientcompiledcode.
Capture now records initial_state_sha256/count/nominalvolume for FUTUREruns; the
first successful run predates that metadata change (don't assert it containsit).

Build21884 failed auto* deduction from NodeGraph TObjectPtr; fixed explicit
UNiagaraGraph*. Build5002 exit0. Capture56403 exit0 liquid-terrain-wet-start-readback,
CaptureLiquidTerrainWetStart.log. Shader28 includes ReadRegisteredWetVolume;
frame6has76821seedIDs<77085 and441inletIDs>=163840. Actual wetstartup proven.
Time .1/.5/1/4/8/12s live77262/77367/74954/74577/85228/100733.
Belowonecell1/80/332/1234/1862/2439; maxpenetrationat12s565.1168cm.
12soutside24,invalidfirstquerynormals7628,maxproposedstep195.727cm,
maxretainedspeed16490cm/s. FAILED. Filled opacity1imageinspected pale,smooth,
invalidpatches; no visual/mass/raft/performanceacceptance.

Expanded existing GridFrameTransfer test constructs grid-frame,complete-gather,
open-sides,wet-start and checks GPUprogram, sixboundaryoverrides, seedarraycounts,
transientownership, unchangedinletarrays/savedpackage. Build47229 exit0;
regression12246 exit0 engine-liquid-wet-start/index.json:8cleanpasses0warnings/
failures11.73s. Python unittest discover test*liquid*.py:12passes .776s including
new test_liquid_initial_state.py exactseed-vs-originaltriangle/hashvalidation.
Contact/map/project hashesstill eefde251.../81f31bec.../01b95fff....
All ownedprocessesterminal. Scopeddiffcheckclean. Nothingtopoll.

NEXT: consistent terrainquery for both particlecontact AND pressureclassification.
Do not revert wetstartup just because itexposesfulldensitycontactfailure. The
registered surface is a known piecewise-linear heightfield with preservedXY;
CPU RegisteredMeshSampler uses bounded3x3 nominalquad search and two triangles/
quad. Export/accelerate that exacttopology for GPUquery (or equivalent consistent
representation with measurederror), not another minor SDF-radius adjustment.
Current coarse SDF remains37³ for24m solids; pressureclassifies viameshSDF,
privatecontactqueries samecoarseSDF. Seedtable is verifiedabovetheexactbed yet
particlesrapidlypenetrate. Inflow/outflow massboundarycondition remainsunverified.
Fullphotographic/motion/raft/performancegates and orderedremainderqueueunchanged.

## September 8 — exact shared terrain query removes sampled penetration

Goal ACTIVE, meaningful code/data/GPU progress, no blocked condition. Fullqueue
incomplete. Report liquid-exact-terrain-contact.md. No promotion/commit.

New physics/scripts/build_south_fork_liquid_contact.py packs exact original
registered XY/diagonals/z into float3 array.40m world-axis patch around0 covers
rotated21m domain + support;12482triangles. Metadata vector0=(x0cm,y0cm,dxcm),
vector1=(dycm,quadcols,quadrows); then six vertices/quad. Query bounded3x3 nominal
quads, two triangles each, centre-first, barycentric tolerance1e-5. Float32
maxheight error across77085seed points.0006495027cm. New test_liquid_contact_triangles
also tests30000off-seed points against originalsampler<.01cm and outsideinvalid.
SourceArt/SouthForkLiquidWindow20260908/triangle_contact_profile.json
SHA46c331b495c55f368c20e38481abe6f9925d541c48928f8c59567c89ddc1c738.

RaftSimRegisteredTerrainQuery.h sharedHLSL used by pressure andparticles. Returns
signedVERTICAL clearance, closestverticaltop, upward triangle normal, stationary
wallvelocity0, valid. Staticheightfieldonly,nooverhangs. C++ LoadRegisteredContact
validatesarraycounts/dimensions thenadds User.River Contact Triangles float3DI.
InstallRegisteredPressureBoundary copies Grid3D_ComputeBoundary, replaces its
singleDIfunction Signature.Name GetClosestPointMeshDistanceFieldNoNormal. Pins
fromactualenginesource: Collision DI,World Position,Closest Distance,Closest
Position,Closest Velocity (withspaces). Reconnectoutputs toownedcustomquery.
AddPrivateTerrainProjection exactvariant uses SAMEHLSL and sets
ProjectedPosition.z+=max(2-distance,0), removesinwardnormalmomentum. No deletion
or speedclamp. Existing8cmsubsteps/max32retained. Pressure still coarse grid but
geometryclassificationmatches exactsurface. OldglobalCollisiondisabled asbefore.

Command RaftSim.LiquidTerrainMomentumReview exact-triangles includes prior
wet-start/open-sides/complete-gather/grid-frame/privatecontact. Name containsall
tokens plus_ExactTriangles_. Pythonflag -RaftSimLiquidTerrainExactTriangles;
also -RaftSimLiquidTerrainContact; captureidentityassertions retained.
Build84207exit0. Capture76771exit0 liquid-terrain-exact-triangles-readback,
CaptureLiquidTerrainExactTriangles.log. ActiveGPUshader contains
RegisteredTriangleBoundary and identicalarraylookup in projection, verticalZfix.
At .1/.5/1/4/8/12s ZERO particlesbelow1mm, zero invalidqueries. Previouswetstart
2439belowcellat12s. Current12s77399live,60outside,median37.3cm/s,max596.6cm/s.
Initialsurvivors29940,inletsurvivors47459. Analysisbinmax6598; inletstillcrowded.

Capture script now SIM_STEPS flag -RaftSimLiquidTerrainSteps=720..3600 (default720).
Actualstateframe captured before presentation-normalizing localframe to720+offset;
simulationframe=-1 untilactualSIM_STEPS thenoldfrozencontrolsrun. Simulation age
metadata usesmin(actualframe,SIM_STEPS)/60. Actualsim still1/60. Addedtrianglehash
toexactcapturemetadata. Build44322exit0 fornewtest, longcapture74248exit0
liquid-terrain-exact-triangles-60s, CaptureLiquidTerrainExactTriangles60s.log.
Complete=true,3600steps,wall350.159sec (NOTgameplaytiming:editor/capture/readback).
60s164079live,ZERObedpenetration,ZEROinvalidqueries,49outside. Median9.727cm/s,
p95speed116.237,max580.58. Upstreamquarter118774particles,Vx7.845cm/s; centre
23075,Vx2.397;downstream5672,Vx1.519. Analysisbinmax84109 (floorlocalpos/32.8125),
notdirectGPUoccupancy. Fullwaterflow is STALLING, notaccepted.12s/60sopacity1
imagesinspected: pale,smooth,patchy,incomplete. ExistingSimCache volumeDIwarning
doesnotinvalidateactualparticle readback; no bakedvolumereplayclaim.

Expanded GridFrameTransfer test hasfivevariants andasserts exactsharedquery in
GPUprogram pluspreviousinvariants. Regression70956exit0 engine-liquid-exact-triangles/
index.json:8cleanpasses0warnings/failures12.662s. Pythonfocused test*liquid*.py:
13passes1.301s. Savedcontact/map/project hashesstill eefde251.../81f31bec.../
01b95fff... . Scoped diffcheckclean. Allownedprocessesterminal, nothingtopoll.

NEXT: actual normal-flow boundary coupling + outgoingvolume accounting. Current
continuousparticlesource does NOT enforce incomingMACgridvelocity; fullgather
averagesnewmomentum intoevergrowingcrowdedcells. Do NOTfixbykillingcrowdedparticles
or restoringarbitraryNQcap. Stockopenfacesare2cells ofEMPTYclassification (code
CustomHlsl13139... Grid3D_ComputeBoundary), notdriveninflow. Inspect actualpressure
solidvelocity enforcement and prescribednormalflux. Consider proper2cellhalo
so native21m facesstayatcorrectlocation (notshifted.66minsidebyghostborder);
21m+4*(21/64)=22.3125m,68cellswouldretain32.8125cm dx, but NOTimplemented/tested.
Wetstartup+exactquery retained. Outflow/stagecoupling, calibratedvolume, real
motion/optics,raftandperformance stillunverified; orderedfullqueueunchanged.

## September 8 continuation — full boundary bindings and outer margin

PROGRESS, goal active, full queue incomplete. No production promotion or commit.
Important correction: earlier boundary-axis diagnosis was WRONG. It read raw
custom-HLSL argument names, missing the module bindings. Actual exposed controls:
Left/Right=X, Back/Front=Y, Down/Up=Z. +X is directly User.Open Outlet=true.
Recent Back=false/Down=true incorrectly closed -Y and opened -Z. Fixed transient
CorrectRiverBoundaryAxes and source factory to Back=true/Down=false. Prior
reports/queue now explicitly correct that interpretation; historical captures
are retained. Contact measurements stand, boundary-flow acceptance does not.

Expanded regression checks six actual compiled control-to-axis bindings, not
only defaults, plus outlet=true. First pattern used Controls instead of the
actual Grid3D_FLIP_FLUID_CONTROLS prefix: 7 pass/1 fail retained in
engine-liquid-boundary-bindings. Corrected final run8/8 clean,13.148s at
engine-liquid-boundary-bindings-final. UE exit0 occurred even with test failure;
always inspect index.json totals.

Corrected-control12s capture47577exit0: liquid-terrain-boundary-bindings-v2,
CaptureLiquidTerrainBoundaryBindingsV2.log,720steps,complete=true,wall33.29s.
77995live,zero sampled bedpenetration across all6ages,61outside,median41.334cm/s,
analysisbinmax6827. Upstream/centre/downstream counts46597/15551/5200,
meanVx21.131/7.181/20.091cm/s. Still crowds/stalls. Image inspected fails.

Implemented opt-in console variant `grid-halo` inheriting exact-triangles.
Only computationalXY expands to2231.25cm and User.Num Cells Max Axis=68.
dx32.8125cm unchanged;2cellEMPTYborder outside native21mfaces. Source arrays,
initial particles, terrain and KillParticlesInVolume physical2100x2100x800 box
unchanged. Capture flag -RaftSimLiquidTerrainGridHalo, requiresContact; asset
token_GridHalo_ asserted. Metadata distinguishes computational vs physical
extents. Readback continues21m region/outside classification. Code in
LiquidTerrainContact.cpp, LiquidFixture.cpp, capture_south_fork_liquid_terrain.py.

Halo capture45150exit0: liquid-terrain-grid-halo,CaptureLiquidTerrainGridHalo.log,
12s720steps,complete=true,wall22.72s (NOTgameplaytiming). Actual pressure dispatch
34x68x24 confirms68x68x24grid. At12s23576live,zero sampled penetration atallages,
111outside,median38.942cm/s,analysisbinmax70. Upstream/centre/downstreamcounts
5406/8184/2900,Vx-22.699/-6.776/28.888cm/s. Initial77238live drains rapidly despite
sources. Margin removes huge inletcrowding but does NOTmaintainflow. Image
inspected fails: smoothpale sheet andedgestrips. Candidateunsavednotaccepted.

Latest build38176pass24.05s. Final engine64237exit0:
engine-liquid-grid-halo/index.json8cleanpasses0warnings/failures14.40s.
GridFrameTransfer nowsixvariants includinghalocell/faceinvariants.
Python13focusedliquidtestspass.94s. Scopedgitdiffcheckclean. Savedcontact,
registeredmap,projecthashes unchanged eefde251.../81f31bec.../01b95fff... .
AllownedUE/buildprocessesterminal; nothingtopoll. Report liquid-boundary-bindings.md.

NEXT implement driven wet ghost normalflux +outgoingstagepressure, notjust
particleinjection. Stock pressure uses SolidVelocity neighbor normal components
in BoundaryAdd; ProjectPressure enforces same components. Shared trianglequery
must keep actualbed stationary. Consider injecting ghostprofile separately in
ComputeBoundary (ownedgraph) usingnativeface stage/normalvelocity arrays; do
notmovephysicalfaces, deletesourcewater, restoreNQcap, orarbitrarilyboostvelocities.
Need actualcumulativeentry/exit/storage, sustainedphysics andvisualchecks.
Fullorderedscenequeue remains unchanged. Thiswasprogress,notblocked.

## September 8 continuation — driven native-face pressure boundary

PROGRESS. Goal/fullqueueactive, notcomplete/notblocked. No assets promoted or
committed. All processes below terminal; no liveUE/build at end.

New generator physics/scripts/build_south_fork_liquid_grid_boundary.py exports
grid_boundary_profile.json under SourceArt/RaftSim/SouthForkLiquidWindow20260908.
SHA40d4201efe001117fb062c0589c42dfb13aca75c018328256c3b7c36e763b9ed.
260float3vectors:headers axisX,axisY,(dxcm,halfwidthcm,zfloorcm),
(dzcm,64,24); then4faces*64columns of(nativefacebedcm,stagecm,inwardnormalcm/s).
Faceswest/east/south/north. dx32.8125cm,dz800/24cm,physical21m,compute22.3125m.
Nativefaceq remapped by overlap*resolvedwetarea, preserving represented native
one-metre totals. Uniformoverlap failedonshallowdrycells; wettransfer resolves
meaningfulflow. Southnativefaces17/20 have1.4903933587e-8/2.4906929000e-8m3/s
butnowetcell; explicitly recorded unresolved4e-8 total, each<1e-7 (float32eps
at1m3/s). Nophantomwetcell. Defaulthelpertolerance0 rejectsanyunsupportedq;
mainexplicit1e-7. Allmeaningfulfluxpreserved. Bed/stage attheactualnativeface,
NOTatghostterrainoutsidephysicalwindow. Peaks2.028/3.088/1.407/.841m/s.
Sourcehasheschecked. Submergedbedinferred/rapididentityunaccepted asbefore.

New consolevariant `driven-boundary`, captureflag
-RaftSimLiquidTerrainDrivenBoundary (requiresContact), inheritsgrid-halo.
In LiquidTerrainContact.cpp LoadGridBoundary readsarray User.River Grid Boundary,
validatescount/finite/headerdims/orthonormalaxes. InstallRegisteredPressureBoundary
addsarray inputtoownedcustomRegisteredTriangleBoundary. Afterexactquery, outside
physicalfaces only, wetghostcells returnDistance=-.01 and grid-local normal
Velocity, zero tangential. ExistingpressureBoundaryAdd andProjectPressure use
normalSolidVelocity. Insidephysical21mexactterrain remainsstationary; particle
contactdoesNOTuseghostquery. Source/initialparticles/retirementunchanged.
Outgoingnormalfluxprescribedtoo, NOToutgoingpressure/stagecoupling. Wetmaskusesstage.
Assetnameincludes_GridHalo_DrivenBoundary_;captureasserts/recordsprofilehash.

12s capture50106exit0: liquid-terrain-driven-boundary,
CaptureLiquidTerrainDrivenBoundary.log,complete=true720steps,wall27.90s.
98224live,0nonfinite/bedpenetration,63outside,median76.827cm/s,mean79.775.
Upstream/centre/downstreamcounts28008/28785/14259,Vx69.202/56.873/93.274cm/s.
Analysisbinmax121at12s vs6827oldnomargin. Count77236at.1s rises98224at12s.
Imageinspected:coverageimprovedbutpalesmoothsheet/corrugatededges,NOTaccepted.

60s capture30385exit0: liquid-terrain-driven-boundary-60s,
CaptureLiquidTerrainDrivenBoundary60s.log,complete3600steps,wall88.19s
(NOTgameplaytiming).119678live,0nonfinite/bedpenetration,84outside.
Mean67.151cm/s,median60.370; upstream/centre/downstreamVx61.446/47.736/70.415,
counts30806/33388/20469. Actualdownstreammotionpersists, notpreviousstall.
Analysisbinslocalfloor32.8125cm:max1010,p9510,24234bins. NotactualNQoccupancy.
MarkeruniqueIDs0..502668. Countnotcalibratedwatermass, occupiedbinsnotliquidvolume.
Imageinspectedpalesmoothwithroughpatches;visualfail. Allsampledagesterrain0penetration.

Latestbuild84650pass17.51s (prior56569/19894alsopass). Finalengine73753exit0:
engine-liquid-driven-boundary/index.json8cleanpasses0warnings/failures15.425s.
GridFrameTransfer7variants, assertsprofile260vectors/unitcollisionvelocityscale/
actualcompiledPrescribedNativeFaceFlux withnormalvelocityinpressurekernel.
Python17focusedliquidtestspass1.013s (newtest_liquid_grid_boundary.py signedoverlap,
wetsupport/dryreject,explicitnoisetolerance,discretefacefluxandsourceidentity).
Scopedgitdiffcheckclean beforefinaldocs. Reportliquid-driven-boundary.md.

NEXT actualgridfacevelocity/pressure/liquidvolumereadback andcumulativephysical
entry/exit; inspectresidual/storagesettling. Currentghost drive improvesmotion
butdoesnotproveGPUfacefluxorvolumebalance. Needoutgoingpressure/stagecoupling,
notmerelyprescribedoutgoingvelocity. Actual68x68x24gridZextent800meansdz33.333cm,
notdx32.8125; generatoraccountsforfacearea. P2G/G2Poperatorusesstockdxscalar—
checkanisotropicZdiscretizationaspartofpressureaudit, don'tassumecubic.
FLIPparticlecountisanuncalibratedmarkermeasure; don'trescaleemissionorpruneparticles
tofakevolumebalance. Finishphysics/motion/optics/raft/performancebeforepromotion.

## September 8 continuation — actual GPU grids expose incompatible projection

PROGRESS, goal/fullqueueactiveincomplete. No productionasset/settings/promotion
orcommit. Lastownedprocessesterminal, noUE/buildprocessleft.

NEW RaftSimEditorLiquidGridReadback.cpp console RaftSim.LiquidGridReadback PATH,
pathmustnew; selectsoneactive_DrivenBoundary_component, systeminstanceID,
TObjectIterator exactUNiagaraDataInterfaceGrid3DCollection class; GTmaplookup,
Varsnonempty/NumCellsXY>=64 skipsunallocateddisabled3x3x3/1x1x1DIs.
ENQUEUE_RENDER_COMMAND proxy SystemInstancesToProxyData_RT, CurrentData->
GetPooledTexture()->GetRHI(). FieldsPressure,Velocity,SimFloat,SolidVelocity_Boundary,
StartVelocity,SDF. GenericDIbbox100cm NOTsimulationworldextent; actualtransform
fromparticle/systemtelemetry. Metadataattributeoffsets/types/tiles/cells/format.
HALFgrids RHI.Read3DSurfaceFloatData emitsRGBA16F,XfastthenYthenZ. R32pressure
mustNOTusethatAPI—itconverts toFP16andoverflows. New pathusesFRHIGPUTextureReadback
perZslice,EnqueueCopy,SubmitAndBlockUntilGPUIdle,Lockrowpitch,copyoriginalfloat32
bytes to.r32f. SourceRHItransitionsUnknown->CopySrc->SRVMask; nofieldwrites.
Headerencodingnowpergrid, runtimePressureIterationsreadwithGetVariableInt.
Readbackblockingdiagnostic,nevergameplaytiming.

capture_south_fork_liquid_terrain.py flag -RaftSimLiquidTerrainReadGrid exports
at0.1s(frame6)andfinalframe, assertsallactivegridsread. Also optional
-RaftSimLiquidTerrainPressureIterations=40..320 setscomponentUser.Pressure Iterations
beforeactivation,recordsdiagnostic; defaultsnotchanged.

Firstcapture54772failedcompleteness becauseunusedplaceholdergridswereincluded:
liquid-terrain-grid-readback. Actualactivegridssuccessful. Afterfiltercapture96779
liquid-terrain-grid-readback-active complete, butR32->FP16pressureconversion
20342overflowvalues. Retainasreadbackfailure, NOTsimulationnonfiniteclaim.
Correctraw32capture23112exit0 liquid-terrain-grid-readback-f32,
CaptureLiquidTerrainGridReadbackF32.log,complete12s,wall28.7105s. Pressurefinite
-341587.59..372269.31, velocityfinite. BinaryrawsixfieldsactualGPU.

New physics/scripts/analyze_liquid_grid_readback.py decodesactualfields. Tests
test_liquid_grid_readback.py verifyfloat32beyondhalfrange, scalartileoffsets,
truncatedbytesreject. At0.1/12sfluidcellcountvol850.669/1020.423m3 (NOTsubcell),
negativeRenderSDFvoxels662.011/719.891m3 (NOTrender-volume calibration).
Registeredinitialwetvolume680.811m3. DoNOTusemarkercountasmass orwholefluidcells
aswater-volumeproof. SDFgrid136x136x48 physicalcrop[:,4:132,4:132] scaled
(21/128)^2*(8/48); solvergrid68x68x24 physicalcrop[:,2:66,2:66].

Actualghostnormalfluxwest/east/south/north41.39637/-45.08677/2.24735/1.47347m3s,
closeprescribedwithinhalffloatprecision. Adjacentcellintegration12s
41.39565/-45.18039/1.87069/1.47344m3s; NOTexactstaggeredflux, solvercollocated.
2/3/3/0drivenghostcellsadjacentSOLIDinnercells; southevidentdeficit. East43driven
ghostcellsadjacentEMPTYat160run. Needterrain/free-surface consistentface support.

MAJOR CONFIRMED OPERATOR MISMATCH: compiled Grid3D_ComputeDivergence uses
(v[i+1]-v[i-1])/(2dx). Grid3D_ComputeGradient similarlycentralp±1/(2dx).
Grid3D_PressureIteration solvesnearest6neighborp±1/dx². Dcentral*Gcentral is
widep±2/(4dx²), NOTthatLaplacian. Source in actual28_GPUComputeScript_3_1_gpu.hlsl
underliquid-terrain-driven-boundary/active_compiled_shaders:
divlines3891..3914,grad4234..4256,pressure~4080..4207.

Pressureconvergencecomparison: separatecapture71040exit0 liquid-terrain-pressure-160,
CaptureLiquidTerrainPressure160.log,complete12s,diagnostic160iterations,wall28.04s.
At12sonall6neighborsfluid:40iterpredivRMS.126225/finaldiv.112642/Poissonresidual*dt
.084305;160iter.121564/.108013/.0000035815. Different evolvedstates, notsame-state
iterationtrace; but160pressureequationconvergeswhilevelocitydivremains.
Strongactualfieldcheckontwo-cellfluidinterior11698cells:observeddivRMS.05387865,
predictedSimFloat-dt*wideLaplacian(Pressure)RMS.05386626;differenceRMS.00042541
consistentFP16velocity/SimFloatstorage. grid_operator_analysis_12s.json records.
Thischangesnextaction: fixcompatibleprojectionoperators, notraiseiterations.

Report liquid-grid-projection-audit.md. Latestbuild11768pass14.74s. Engine10770
exit0 engine-liquid-grid-readback/index.json8cleanpasses0warnings/failures16.06s.
Python20focusedliquidtestspass1.09s. Scopedgitdiffcheckclean beforefinaldocs.

NEXT implementconsistentpressure/divergence/gradientandfaceboundarysupport,
includingP2G/G2Psampling andanisotropicdx32.8125,dz33.333cm. A MAC/staggered
finitevolumeapproachisreasonable, but don'tchangeoneoperatoralone andpretend
collocatedvelocitiesarefacevelocities. Alternatively compatiblecollocatedmatrix
mustaccountactualD*Gandboundarymask, checkerboardnullmodes. Realwet/drystage/
terrainfractionsneedconsistenthandling. Reuseactualgridreadbacktoverifyresidual,
divergence,transport/volumestorage andtimecontinuity. Thenwateroptics/motion,
raft/performanceandfullorderedscenequeue. DoNOTpromote160iterationsasafix.

## September 8 continuation — compatible projection now survives actual GPU update

Full app goal ACTIVE; South Fork still incomplete. No production asset changes,
promotion, commit or completion claim. No agents. Report: liquid-compatible-projection.md.

New CPU reference physics/scripts/liquid_compatible_projection.py solves the
collocated masked composition -D M G with anisotropic h=(32.8125,32.8125,800/24)cm.
M fixes center-solid and axis-neighbor-solid velocity components, priority matching
stock ProjectPressure (X/Y negative then positive; Z positive then negative).
Pressure zero on nonfluid cells. Matrix-free PCG, no particle pruning or speed
clamp. On earlier pressure-160 snapshot:84 iterations, relative residual9.4598e-8,
divergenceRMS.1585966→1.5003e-8/s, fixed changes0. Saved reference output
liquid-compatible-projection-reference/report.json. Not production/performance.

GPU implementation new RaftSimCompatibleProjection.h included by
RaftSimEditorLiquidTerrainContact.cpp. New console variant compatible-projection
implies driven-boundary and all previous variants. Capture script flag
-RaftSimLiquidTerrainCompatibleProjection; asset _CompatibleProjection_.
Still uses collocated P2G/G2P, NOT MAC or cut-cell fractions. XY68cells, two-cell
halo, original physical21m domain and source arrays unchanged.

Patch actual module custom HLSL only, private copies:
* Grid3D_ComputeDivergence: add BoundaryGrid input bound Emitter.TransientGrid,
  D of constrained velocity. Insert new input BEFORE dynamic Add sentinel;
  Signature/input ordering otherwise crashes history compiler.
* Grid3D_PressureIteration: active branch contains FluidCellCount AND
  GetOutputGridFloatValue (raw DI method, NOT GetOutputFloatValue). Solve ±2
  masked neighbors/(4h²), explicit PressureGrid.SetFloatValue required. SOR
  saturate(Relaxation)+1 unchanged. Ignore unused Jacobi branch.
* Same pressure dispatch: x=(t/2)*4+t%2+2*((y/2+z/2+(IterationIndex % 2))%2).
  Pressure68x68x24 dispatch34x68x24. Input name needs whitespace before % or
  Niagara token parser fails replacement to In_IterationIndex.
* Unsuffixed Grid3D_ComputeGradient bound PressureGrid: ONLY ScalarIndex input
  branch; other matching S_right branch computes vector magnitude, leave it.
* Grid3D_ExtrapolateVelocity001 (post-project only): custom branch MUST have
  Velocity input AND GetPreviousVector4Value AND TotalWeight. Integer-grid and
  legacy indexed-grid branches are inactive, leave them. Preserve corrected
  component if centerSOLID or ±axis neighborFLUID; extrapolate outside support.
Final expected patches D1 P1 G1 colors1 extrapolate1.
Markers CompatibleMaskedDivergence, CompatibleMaskedPressure,
CompatibleWideStencilColoring, CompatibleAnisotropicGradient,
CompatiblePreserveProjectedSupport; verified in actual GPU program.

Retained failures V4/V5 wrong scalar-vs-vector gradient filtering; V6 input
sentinel ordering assert; V7 actual GPU parser error (verified ownedPID11460
stopped); V9–V11 inactive extrapolation branches. All terminal, no assets saved.
V8 first complete12s: zero penetration, mean70.54cm/s, but finaldiv.08123/s
vs pressurepredicted.01685/s. Post-extrapolation overwrote corrected support.
V12 fixes that: prediv.2167685, residual*dt.0168260, finaldiv.0168287,
prediction difference.0004105/s (FP16 storage).103403 exactbedprobes,0missing,
0penetration/nonfinite; mean61.857cm/s, regionalVx50.326/37.389/66.704.
V12capture30.157s wall, NOTFPS. Sourceopacity0 nearlyblack; opacity1 palefoam,
still visuallyunacceptable.

New analyzer physics/scripts/analyze_liquid_compatible_projection.py uses actual
maskedanisotropicmatrix. Do NOT use old nearestPoisson metric on newcandidate.
Reports allfixed error AND pressure-supportfixed error: outside pressure stencil
extrapolation still alters components. On support max.0625cm/s (halfprecision).
V12 report compatible_audit_support_12s.json; older compatible_audit_12s.json
lacks support-specific field. Raw grids retain original R32pressure/FP16others.

Diagnostic160iterations: liquid-compatible-projection-pressure-160, complete12s,
28.487s wall. Prediv.2187278, residual*dt9.7893e-7, finaldiv.000420635,
predictiondifference.00042062/s. Unlike oldstock, actual velocity now converges
to halfprecision. Different evolvedstates, NOTsame-snapshotiterationtrace.
No productioniterationincrease.

Default40iteration60s: liquid-compatible-projection-60s, complete3600steps,
87.478wallseconds.123484exactbedprobes,0missing/nonfinite/penetration,85outside,
mean56.828cm/s, regionalVx41.000/39.269/57.736.31,435fluidcells,prediv.236639,
residual*dt.017239,finaldiv.0172444,predictiondifference.0004412/s. Marker counts
NOTwatermass. Storage/throughputstillunverified. Opacity-oneimage paleuniform,
rectangular fixtureedge, noacceptance.

Engine8cleanpasses engine-liquid-compatible-projection/index.json17.243s.
Expanded transfer test loops eighthcompatiblevariant plus sourceunchangedchecks.
Python17test_liquid*.py pass1.603s, includes adjoint, CPUprojection, audit and
wide-stencilcoloringcoverage. Later GPUcompilegate added: command now waits
WaitForCompilationComplete(true,false) and requires DidScriptCompilationSucceed
for ParticleGPUComputeScript before installingcandidate; testschecksame.
Build68427pass17.87s. Final gate regression session24503 launched; inspect
engine-liquid-compatible-gpu-gate/index.json and poll if still live.

Saved hashes rechecked unchanged: contact EEFDE2513997E3CFA1206ACC1BC053B6A3729280CFA7C5EAE9DF6230DC714122,
level81F31BEC7BA8683E3A7479F17333419B6D32EEB277DE5630F098D41FDF705AD7,
project01B95FFFDEC2649864C397A9A7C786D083371E469EFBACE3505E0E0AE2AC3B44.
Scoped gitdiffcheckclean before final gate/docs; no commit.

NEXT calibrate actual liquidvolume and source/outletstorageflux, outgoingstage
coupling and terrain/wetface support. Current collocated binaryboundary normal
drive improvesmotion but is not freeoutgoingpressurecondition or cutcellconservation.
Preserve compatibleprojection and verify anyboundarychange against itsactualmask.
Then tune realwateroptics/foam/motion (currentopacity0 vs1 controls notshadingfix),
continuoussingle-surfaceintegration, raft and realgameplayperformance. Full ordered
scenequeue remains; don't promote a numerical diagnostic as realistic South Fork.

Final gate follow-up: engine-liquid-compatible-gpu-gate initially7pass1fail
because disabled Grid3D_FLIP_Secondary emitters have no compiledresource. Corrected
gate/tests to enabledhandles ONLY; no runtimephysics change. Build99748pass17.73s.
Engine session74879 terminalexit0; engine-liquid-compatible-gpu-gate-v2/index.json
8cleanpasses0warnings/failures16.403s. LatestPython17tests pass1.054s, scoped
gitdiffcheckclean. ALL owned engine/build sessions terminal; no live work to poll.
No new production asset writes or commits. Full goal remains ACTIVE/incomplete.

## September 8 outgoing-stage continuation — LIVE GPU compile, do not duplicate

Previous turn PROGRESS; this turn implements native downstream-stage pressure
candidate, CPUreference/audit/tests. FullgoalACTIVE, noacceptance/promotion/commit.

IMPORTANT LIVE process: capture exec session65575, UnrealPID34328, started22:30:35UTC.
Last revalidated22:44:19UTC viawrite_stdin (stillrunning) andGetProcess.
Command capture_south_fork_liquid_terrain.py -RaftSimLiquidTerrainContact
-RaftSimLiquidTerrainOutletStage -RaftSimLiquidTerrainFixedOverhead
-RaftSimLiquidTerrainReadGrid -RaftSimLiquidTerrainDumpActiveShaders
-RaftSimLiquidTerrainLabel=liquid-outlet-stage-v4.
Log docs/reconstruction-review-2026-09-07/CaptureLiquidOutletStageV4.log;
outputliquid-outlet-stage-v4 stillnoresults. DoNOTlaunchUE/buildwhilelive.
Firstnextactionpoll65575; observationtimeoutisnotterminal.
Workers3432,35356 parent34328, workingdirs
C:/Users/salsi/AppData/Local/Temp/UnrealShaderWorkingDir/DB76C1EE4B9EA6749A0276BFFCCD4092/0
and/1. Temporarilyemptydirsincorrectlysuggestedstall; recheckfoundnew
WorkerInputOnly.in files22:41:32UTC (22293/38095bytes). ThereforeprocesswasNOT
stopped/restarted. CPUstillincreased at22:44:19:workers42.77/116.30s,UE212.08s.
Coldcompilation isverylong; noerrorreported/logprogressafterregisteredgraph.
Capturewallbound480s startsbeforecompile, mayexitwithtimeoutaftercompilefinishes;
thenretainfailureandreruncachedshaderonlyafterterminal. Do notcallsuccess.

LatestBUILTcode: build68745PASS17.25s. SourceeditsSINCEbuild:
* Expanded engine transfer test to ninthoutlet-stagevariant.
* Two-phasecompilewait incommand: WaitForCompilationComplete(false,false) first,
  thenlog"Momentum graph compilation finished; waiting for current GPU shaders",
  thenWaitForCompilationComplete(true,false). This ispreparedNOTbuilt/tested.
  EngineWait(true) collectsinheritedGPUresourcesBEFOREcompletingactivegraphcompile,
  soseparatingphasesmayavoidwaitingobsoletehandles; currentlongwaitcausenotproven.
Allotherbuild/capture handles terminal. V1–V3 installationsfailed,noGPUresults.

Implementation:
new RaftSimOutletStage.h sharedinlinequery+safeAddCustomInput helper.
Sameprofile260float3nativegrid_boundary_profile.json unchanged, gravity980cm/s²
verifiedactiveHLSL. Outgoingcolumns row.z<0: ghostcellsoutsidephysical21m and
aboveprofilebed aretype3externalstage (NOTsolid/unknownfluid), pressure
980*max(stage-z,0)cm²/s². Abovelevelatmospheric0. Incomingcolumnsretainnormal
fluxmovingghost; noextra source/delete/velocityclamp. Cornersunchanged.
Profilebed/stagemodelderived/submergedbedinferred, notnewcapturedsurvey.

InstallRegisteredPressureBoundary(...OutletStage): nativeghost velocity condition
changedonlyoutletvariant to row.z>=0. Add StageProfile array andStageWorldPosition
to final CustomHlsl RetBoundary classifier; sharedquery setsRetBoundary3 outside
atoutgoingprofile. Exactregisteredterrain queryinsidephysicaldomainunchanged.
PositionreadusesoriginalWorldPosition source; arrayusesexistingBoundaryRead.
CompatiblePressure(...OutletStage): addedStageProfileUser.RiverGridBoundary read.
Pressuretype3assignedexternalhydrostaticvalue; fluid±2neighboriftype3 usesexact
boundaryvalueinrhs (not staleoutputgridread); pressureunknownsonlytype0.
Worldgridlocalindexposition=(p+.5)*h -1115.625XY, Z350+(p.z+.5)*800/24.
Velocitymobilitystillonlysolidtype1fixed; postextrapolationpreservessupport.
Markers NativeOutletStageClassification, NativeOutletStagePressure.
Newconsoleoutlet-stage=>compatible=>previouschain, asset_OutletStage_.
Captureflag-RaftSimLiquidTerrainOutletStage andoutlet_stage_candidate metadata.

PressureBoundaryGrid pin linked through NiagaraNodeReroute_8 (V3diagnostic).
DuplicateTypedMapRead nowfollowsunambiguousrerouteswithvisitedcyclecheckbefore
cloningactualparameterMapGet. ThisresolvespreviousV1–V3missingStageProfilesource.
Noothernativearraysorassetsmodified.

Pythonreference liquid_compatible_projection.py nowacceptstype3 plus explicit
boundary_pressure, rejects missing/invalidexternalpressure. RHS includes
D M G(pBoundary), returnfullpressure. fixedmaxsupportsnosolidcase. New
liquid_outlet_stage.py independentlycomputesexpectedknownmask/hydrostaticpressure
at68x68x24centers. analyze_liquid_compatible_projection.py --stage-profile PATH
reportsactualtype3classificationmismatch andpressuremaxerror; pressure residual
includesknownstagepressure. nonfluid_pressure_max renamednonfluid_nonstage_pressure_max.

22test_liquid*.py pass1.265s; addednonzeropressureconvergence/requiredvalues and
outgoing-onlyghostclassification, hydrostaticgradient/abovestagezero, invaliddims.
Referenceoutputliquid-outlet-stage-reference/report.json runsfromactualV12grid
withoutgoingboundaryreplaced:89iterations,residual9.0407e-8,div.01682865→7.0267e-9/s,
fixedchange0. CPUreferenceonlynotenginefield. Newdocliquid-outlet-stage.md, queueupdated.
Scopedgitdiffcheckclean; noengine/outgoingstagevisualclaim.

NEXT waitcurrentcompileauthoritatively; inspectcoldshaderresult/errors. Thenbuild
preparedtwo-phasewait+enginetestschanges whennoUElive. RunoutletstageactualGPU
readback andstage-profileaudit, comparepressuretype3andphysicalcontact/flux. Do
notrelaxpressurecompatibility. Addfreshengine9varianttestexecution. IfshortGPU
valid,longrun60swithnormal40iterations. Calibratedvolumestorage/exit accounting
stillopen; opticsopacity0black/opacity1paleuniformnotresolved. Fullorderedscene
reconstruction/realism/crew/performance/cleanup/releasecommitqueueunchanged.

## September 8 continuation: outlet GPU success, optical frame fixes, exchange mismatch

Full app goal remains ACTIVE and unbounded. No promotion or commit. No genuine
blocker, no subagents. All engine/build/capture sessions from this continuation
are terminal; do not poll the old V4 session 65575 or the 60s session 21380.

### Outlet-stage result and shader retry fix

The previous V4 was an infinite shader-error retry, not a slow successful compile.
Worker output showed `stagefloat3(...)` declarations: FString ReplaceInline's
case-insensitive POSITION substitution also replaced the suffix of stagePosition.
RaftSimOutletStage.h now explicitly uses ESearchCase::CaseSensitive for PROFILE
and POSITION replacement. Verified owned V4 PID34328 was stopped; no GPU result.
New engine generated-string regression prevents recurrence. Two-phase graph/GPU
wait and ninth outlet variant are built. V5 capture51872 completes;9engine tests
67593 pass. These handles are terminal.

Actual V5 at12s:4142 stage cells,0 classification mismatches, max pressure error
.0718713cm²/s², D-rms .191478→.022555/s, residual prediction .022554/s,
predicted/actual RMS difference .000394/s.89564 exact bed probes,zero penetration,
missing queries or nonfinite states. Fixed-support velocity error .015625cm/s.

Actual60s capture21380 completes in83.505s diagnostic wall time. Directory
liquid-outlet-stage-60s, pressure_stage_audit_60s.json:4142 stage cells,0 mismatch,
same .0718713pressure error, prediv .206384→.022238/s, pressure residual*.dt
.022236/s, prediction difference .000403/s, fixed-support error .0625cm/s.
98673bed probes,0 penetration/missing/nonfinite. Mean speed56.122cm/s,
upstream/centre/downstream Vx43.972/34.148/33.630cm/s. These are not mass or FPS.
See liquid-outlet-stage.md. Python audit now handles all-fluid/no-fixed subsets.

### Actual material diagnosis and transient corrections

New RaftSimEditorLiquidMaterialInspection.cpp exports source graph read-only via
RaftSim.InspectLiquidMaterial material-path new-json-path. Source graph has114
nodes including functions; local diagnosticliquid-sdf-material-graph.json contains
engine template code and must not be treated as a release redistribution asset.
The inspection's Quit command did not exit the editor. After verifying command
line, stopped only completed inspector PID41156/session46144. No asset saves.

Source /NiagaraFluids/Materials/Grid3D/M_WaterSDF:
- Scattering = Scattering.rgb*Scattering.a*volume.g*Whitewater; actualMIDWhitewater0
  zeroes ordinary water scattering. Roughness constant0. Opacity0nearlyblack,
  opacity1pale diffuse coating, not foam.
- bTangentSpaceNormal=0, but normal output is grid-local SDF gradient. Gridyaw
  158.434789degrees therefore gives wrong highlight/reflection directions.
- Raymarch Custom_0 calculates WorldDepth=SceneDepth/dot(LocalRayDir,CameraDirectionVector).
  CameraDirectionVector is world-space. At oblique camera local(-17,-23,12),
  focus(0,0,2.5), dot is negative and valid water hits are discarded.

New RaftSimLiquidOptics.h helpers:
RaftSimCreateLiquidScatteringReview duplicates source UMaterial to transient,
connects existing RGB*alpha coefficient directly to SingleLayerWater output and
adds River Roughness parameter(default0). Absorption, mask, WPO, PDO preserved.
RaftSimCorrectLiquidWorldNormal adds Custom normal transform using actual
LocalToWorld0..2 parameter rows; clears Custom's default Inputs before adding4.
RaftSimCorrectLiquidRayFrame changes the mixed depth dot to
SceneDepth/max(dot(WorldRayDir,CameraDirectionVector),1e-6).
No physics changes, extra surface or texture layer. No simulated foam yet.

Console RaftSim.LiquidTerrainBaseScatteringReview [world-normal|world-frame]
only accepts existing transient _OutletStage_ system and one transient ownedMIC.
Snapshots effectiveuniformparams, reparents copiedMIC to transientparent, restores
uniformparams, PostEditChange and waits asset/shader compilation. Preservesvolume
texture bindings. Refuses saved/engine material mutation. ScatteringControl
strength roughness changes only correctedruntimeMID Scattering.a andRiverRoughness.

Capture script additions:
-RaftSimLiquidTerrainOpticsSweep, -RaftSimLiquidTerrainBaseScattering,
-RaftSimLiquidTerrainWorldNormal, -RaftSimLiquidTerrainWorldRay,
-RaftSimLiquidTerrainFixedOblique (instead of FixedOverhead).
Fixed camera established BEFORE simulation; simulation frozen after12s.
Baseline sweep opacity0/.1/.5/1 x exposure-10/-14/-18. Base-scattering sweep uses
opacity0,roughness.12, scattering.0001/.001/.01 percm x exposure-10/-12/-14.
RuntimeMIDreports assert new RiverRoughness exists. No movement-after-freeze.

Completed actual captures, all terminal:
liquid-optics-opacity-exposure (64762),29.912s: exposure cannot fixblack/opaque.
liquid-optics-base-scattering (43383),36.010s: transparentbluegreen nowvisible.
liquid-optics-world-normal (12224): changed highlights inoverhead.
liquid-optics-world-normal-oblique (48058),30.230s: waterinvisible due depthbug.
liquid-optics-world-frame-oblique (41114),34.756s: waterrestored atsameobliqueview.
Viewed optics_01.png shows glossy cyan liquid with real depth/bumps but exposed
rectangular computational edges, nofroth/breakup; NOT photographic acceptance.
Do not equate this21m fixture with a reconstructed/accepted shippingrapid.

First base engine suite10passes17.768s. Initial worldnormal suite47431 crashed
at testline71: Custom constructor's extraemptyinput was dereferenced after a
non-blocking countassert. Fixed installerInputs.Reset plus earlyreturn/nullcheck.
Failedlog EngineLiquidWorldNormal.log retained. Latest build20878 PASS16.37s;
latest actual suite41218 terminal0:engine-liquid-world-frame/index.json has
10cleanpasses0warnings/failures17.940s. No C++ edits after build20878.
See liquid-optics-world-frame.md. Source system/level/uproject hashes unchanged:
EEFDE2513997E3CFA1206ACC1BC053B6A3729280CFA7C5EAE9DF6230DC714122
81F31BEC7BA8683E3A7479F17333419B6D32EEB277DE5630F098D41FDF705AD7
01B95FFFDEC2649864C397A9A7C786D083371E469EFBACE3505E0E0AE2AC3B44

### New actual exchange diagnostic — unresolved physics

analyze_liquid_exchange.py and test_liquid_exchange.py use actual velocity at
physicalface midpoint(averageghost+inner) over native-profilewet aperture. Report
partialcell and centre-selectedwholecell separately; profile speeds were
normalized against wholecellarea, so partialintegral is NOT nativeQ.
V1exchange_aperture_audit_60s.json had ambiguous native_target names, retained
but superseded by exchange_aperture_audit_60s_v2.json. V2wholecell valuesm³/s:
face   prescribedprofile   actualmidpoint
west       41.412585          36.803781
east      -45.103418         -15.680268
south       2.247995           2.052491
north       1.473978         -26.138466
net          .031141          -2.962462
Partialaperturenet -4.215257. Neither is storage loss: actualmovingwet aperture
and temporal fluxintegral unmeasured. Strong lateral redistribution contradicts
acceptance of native/3D flowhandoff even though pressureboundarymatches.
26focused test_liquid*.py PASS1.182s. Scopedgitdiffcheckclean.
See liquid-exchange-aperture.md. Do not clamp exits to desiredQ or callNmarkersmass.

NEXT investigate actual surfacelevel/storage and lateral outlet flow; obtain
actualtime-integratedwetaperture/exit accounting. Then explicitadvected
aeration/foam/breakup, single-surface full-scene integration, continuouscamera
motion and performance. SourceSDF texture currentlyexports onlyredSDF; do not
assume greenchannel is valid simulatedfoam. The raymarch also lacks earlyexit
at tmax in its loop (potential renderingcost issue to measure, not yetchanged).
Capturedrig is not photometric calibration; no motionclip or normalgameplayFPS
acceptance yet. Full SouthFork→Colorado→Pacuare→Futaleufu, otherwater/crew/cleanup/
releasecommit goal remains active. Do not narrow it or mark these diagnostics done
as a substitute for scene completion. No owned running processes remain.

## September 8 continuation — actual aperture and centered P2G

PROGRESS, not full acceptance. Full app goal and queue remain active, no blocker,
no production promotion, no commit. See liquid-surface-aperture.md and
liquid-centered-transfer.md for exact methodology, retained failures and results.

New Python analyze_liquid_surface_exchange.py + four tests measure actual negative
render-SDF intervals and interpolated velocity, clipped above native bed, including
disconnected intervals. Baseline60s shows severe edge erosion; excessive north
exit remains one32.8125cm cell inside. Reports under liquid-outlet-stage-60s:
sdf_exchange_60s.json, sdf_exchange_60s_inset.json, sdf_exchange_0p1s.json.
Not conserved-volume measurement or temporal mass budget; inset uses boundarybed.

New optional pic-flip=[0,1] argument on outlet-stage/centered-transfer installs
only a transient control override. Telemetry filter now includes actual spaced
PIC FLIP Ratio attribute. Capture asserts requested ratio matches actual cache.
Old transfer pureFLIP1 is unstable: p95speed4395.36cm/s by12s, N27443. REJECTED.
Do not raise the saved .75default. Capture liquid-transfer-flip-one retained.

Actual compiled NQ insertfloor(Unit*NumCells) vs velocitycenters Index+.5 exposed
old equal-weight [-1,0]^3 gather's halfcellbias. New centered-transfer variant
gathers [-1,1]^3 and uses centeredtentweights with actual rotated anisotropiccell
metric, retaining full neighborcount and correctedvelocitybasis. Single-cell
static alternative is not selected; actual compiled GPU marker checked by tests.

IMPORTANT PowerShell split unquoted -RaftSimLiquidTerrainPicFlip=0.75 into =0 .75.
First liquid-centered-transfer run is actualPIC0, correctly recorded, NOTmatched
.75 A/B. Quote decimal-valued nativeargs. Corrected liquid-centered-transfer-075
reportsactual .75 allsamples. Meanlocaldownstream at1s82.710cm/s (old35.585),
at12s89.552(old39.599), p95speed216.50. No detectedbedpenetration. Divergence
.021024/s, pressure-residual mismatch.000595/s; stage4142cellsmatch. 12sdiagnostic
wall43.972s, notFPS. projection_12s.json retained.

60s liquid-centered-transfer-075-60s alsoactual .75, complete87.770swall including
opticalsweep/blockingreads. N80276,80188exactbedprobes,0missing,0penetration>1mm,
0nonfinitevelocities,88outsidephysicalboxpendingretirement. Meanlocalvelocity
(75.391,14.976,-3.163)cm/s,p95speed205.447. Divergence.019786/s,residualdifference
.000585/s,4142stagecells0mismatch,stagepressuremaxerror.071871cm²/s².
projection_60s.json and sdf_exchange_60s_inset.json retained. SDFinsetQm³/s:
west+37.418,east-15.577,south+1.736,north-21.274. Notamassbudget.
Actual optics_01.png inspected: glossycyanblobbypatchwithrectangularedges, NOT
photorealwhitewater. Noacceptedfoam,fullsceneintegration,motioncliporFPSyet.

Latestbuild6960 PASS18.76s. Suite62005 terminal0:
engine-liquid-centered-transfer/index.json10cleanpasses0warnings/failures20.94s.
Expandedgridframetest includescentereddefault andcenteredpic-flip=1. Newindependent
test_liquid_transfer.py verifiesbias,centeredquadrature,constant/affinepreservation,
rotatedanisotropicmetric. 34focusedPythonliquidtestsPASS1.244s.
Saved system/map/uprojecthashes unchanged from preceding checkpoint.
Sessions32300,88513,6960,62005,14879,91797,86066 allterminal; noownedUErunning.

NEXT: actual temporal exchange/storage + boundarymomentumconsistency, notmore
blindblend/velocitytuning. Virtualghostinflow still onlynormalvel, whereas source
particlesretain tangentialnativevel. FluxweightedlocalsourceXY west173.457,28.656;
south171.445,97.918;north116.558,-63.753cm/s. Do notclaimrestoringtangentfixes
northexit withoutA/B. Thenexplicitadvectedfoam/breakup,coherentsurfacereconstruction,
fullsceneone-surfacehandoff,normalgameplayperformanceandvisualchecks. Fullqueue
SouthFork→Colorado→Pacuare→Futaleufu,otherwater/crew/cleanup/releasecommit unchanged.

## September 8 continuation — vector handoff, convergence, actual zero foam

Previous turn classified PROGRESS. This turn also PROGRESS: implemented a real
boundary handoff correction and ran actual GPU/reference A/Bs. Full goal remains
ACTIVE; no blocker, scene acceptance, promotion, commit, or scope reduction.
Detailed evidence: liquid-vector-boundary.md.

New `vector-boundary` variant follows centered transfer and outlet-stage but
loads `grid_vector_boundary_profile.json` v2 (516 float3 rows). First260 rows
exactly match v1. Appended local XYZ vectors keep the conservative normal speed
and native interpolated momentum/depth tangent; no exact tangential momentum-flux
claim. Builder --with-tangent refuses overwrite and verifies geometry/hydraulics.
SHA256 02DFEB80F5E21C17D8BBB2597B911C6F283B06EE1F121B04FDDBE731E44DC495.
Original v1 retained. Loader validates schema/axes/count/normal-vector equality.
Capture flag -RaftSimLiquidTerrainVectorBoundary; quote decimal blend flags.

Actual 60s capture `liquid-vector-boundary-60s`, blend .75, pressure40 completes
89.020s diagnostic wall. N80508, mean local XYZ(75.476,16.312,-3.101)cm/s,
p95speed206.821cm/s,80434exactbedprobes,0missing/penetration/nonfinitevelocity.
New analyze_liquid_vector_boundary.py verifies960inflowcells/2880components.
Initial vector_boundary_audit_60s.json assumed half round-to-nearest and falsely
rejected646components. Retained. V2 audit checks exact half nearest OR toward-zero
conversion, not loose velocity tolerance: all2880actualcomponents match truncation
towardzero;1972also nearest. Rawmaxerror .118428cm/s. Compiled inflow binding is
correct. Tests reject zero/missing tangent. RHI actual chosen adapterRTX3060Laptop;
generic automation-device metadata listsAMD but isn't the selected D3D12adapter.

Pressure audit40: finalD .020224/s, predictedresidual .020217/s, difference
.000588/s. Native4142stagecells0mismatch,maxpressureerror .071871cm²/s².
CPU reference now has --input-velocity StartVelocity to solve same preprojection
input (default Velocity retained). `converged_projection_reference` undercapture:
72PCGiters,relres8.988e-8,D2.044e-8/s;velocity differsGPUby .321cm/sRMS.
Instantaneouswetaperture flow almostunchanged by this reference correction.

Actual higher-iteration A/B `liquid-vector-pressure160-60s` completes97.427s
diagnosticwall, actualiterations160, blend.75. N79846,meanlocalXYZ
(78.817,14.585,-3.338)cm/s,p95speed208.523,79767bedprobes,0missing/penetration/
nonfinitevelocity,79outsidephysicalboxpendingretirement. D .000606/s vs predicted
pressure residual .000000863/s; remainingdifference .000606/s is half-storage
scale. Native4142stagecellsmatch. No production iteration increase orFPSclaim.

SDF inset Q m³/s at60s, same originalboundarybed/stagereference, NOTmassbudget:
face       pressure40     pressure160
west         +37.354        +37.212
east         -15.040        -16.434
south         +1.546         +1.634
north        -21.549        -20.298
Full-vector inflow and pressure convergence do NOTsolve lateralexchange mismatch.
Actual optics_01.png atboth60sruns inspected: glossycyanblobby boundedpatch,
exposedrectangularedges, nofroth. NOTphotorealwhitewater orfullsceneacceptance.

NEW definitive foam-path evidence: vector-boundary capture active_compiled_shaders/
28_GPUComputeScript_3_1_gpu.hlsl stage17/Grid3D_SetRTValues around5120 writes SDF
toR and CONSTANTZERO toG/B/A. Around6640 Redbinds ConvolvedValue, otherchannels0.
Current material foam channel has NOsimulatedfoam. Do not tune multiplier as a
substitute. NEXT rendering work: explicit advected aeration/foam and coherent
surface reconstruction on the actual stable 3D field; keep lateralhandoff/storage
and fullscenephysicalacceptance open. Avoid blind pressure/blend/speedtuning.
Review source stage17 DI ownership/read-write behavior before adding history;
do not assume in-place SimRT sampling is safe or greenalreadycontainsaeration.

Latestbuild79333PASS16.15s, engine suite46280terminal0:
engine-liquid-vector-boundary/index.json10cleanpasses0warnings/failures21.24s.
38focusedPythonliquidtestsPASS1.304s. SavedNS/map/uprojecthashes unchanged.
Sessions79333,46280,1046,52119 allterminal. CPU reference exited0. NoownedUElive.
Full SouthFork→Colorado→Pacuare→Futaleufu,otherwater/crew/cleanup/releasecommit
queue is unchanged and incomplete.

## 2026-09-08 evening — advected foam storage and single-surface shading

PROGRESS, full goal ACTIVE. No blocker, production promotion, final commit or
scope reduction. Detailed current evidence: liquid-advected-foam.md. No owned
UE/build process is live; engine suite95610 exited0 and all captures terminated.

New RaftSimLiquidFoam.h, foam variant and -RaftSimLiquidTerrainFoam implement
local-velocity backtraced volume coverage with4s decay, surface-band vorticity/
compression generation, solid/edge suppression and exact source-decay reaction.
Read previousSimRT.g in stage16 (afterX SDF); carryRiverFoam through stage17 and
write newSimRT.g. Original stage numbering assumption was wrong:ConvolveAxis001
isX; unsuffixed isY. Source/contact/velocity equations unchanged.

Retained failures:
- liquid-advected-foam-v1: addingRiverFoam shiftedSDFtoindex1; Y/Z stillread0.
  SDFbecamenonnegativefoam. analyze_liquid_foam.py rejects it.
- v2/v3: indexoverride read downstream/reusedoverrideparammap causingstack
  overflow. Corrected by readingBEFOREoverrideSet, plus graphcycle guard.
- v4/v5: correctSDFbut maxfoam~.019(one-step only). Direct renderedvolume
  readback PROVESPF_R16F/configuredRTF_R16f; greenwasdiscarded.
- v6: ownedvolume explicitlyRGBA16f+TF_Bilinear; actualGPUred/green EXACTLY
  matchSDF/foam. At12sfoammax.4172363. Nonfinite0. Sourceassetsunchanged.

RaftSimLiquidOptics.h newRaftSimConnectLiquidFoamOptics usesWhitewateroutput
atactualrayhit, blendsBaseColor/.7roughness/opaqueBSDFonSAMEsurface. Always
derive normalfromSDFred(foaminGisnotnormal). Uses correctedworldnormal/ray.
ConsoleBaseScatteringReview foam-world-frame guards_Foam_; FoamControl0..8
operatesruntimeMIDonly. CaptureFoamOptics requiresFoam+WorldRay+WorldNormal+
BaseScattering+FixedOblique/OpticsSweep. NewFoamStrengthSweep uses0/1/4 with
fixedscatter.001/cm,roughness.12,exposure−10; gain4diagnosticonly.

Actual liquid-advected-foam-60s:3600steps,blend.75,pressure40,93.58sblocking
diagnosticwall(NOTFPS). N80629,80545exactbedprobes,0missing/penetration/nonfinite
velocities,meanspeed90.760cm/s. Foam0..0.494629,SDF−10.046875..49.1875cm;
renderPF_FloatRGBA10,redSDFandgreenfoammaxdifference0,allfinite.
foam_audit_surface_60s.json:highesttopcrossing14460columns,meanfoam.009425,
p95.05730,max.19698. VolumemaxisNOTvisiblecoverage. Supportsnextworkseparating
submergedaerationfromfree-surfacefoam,notjustincreasingwhitegain.
Frozenstrength1changes78614pixels>1levelvsoff;gain4changes100450.
Observedopticsandmotionframesremaincyan/glossy/pillowywithrectangularwindow
edgesandangularuntexturedterrain. NOTphotographicwhitewateracceptance.

ThirtynativePNGframes,last2s(stride4steps) assembledlosslesslyto
liquid-advected-foam-60s/motion.png(animatedPNG) byencode_liquid_motion.py.
All30decodedRGBframesmatchsourcehash-verifiedimages. Noduplicateadjacentframes.
Playback15fpsNOTgameFPS. Individualframes0/15andoptics01/02viewed; nofluid
trajectoryorfullanimationacceptancefromimagechangealone. Newmotion_report.json.
Existingtmp/water-motion-review-deps/avhasreadpermissionsfailure; noinstallor
permissionchangesattempted, PillowAPNGusedinstead. EncodingisnotAIimagery.

44focusedPythonliquidtestsPASS1.384s. Finalbuild23869PASS16.23s.
engine-liquid-foam-optics initially9pass/1fail: testincorrectlycheckedunused
custominputDIdefaults. CorrecttesttargetsactualcompiledSystemSpawnSimRTbinding;
runtimeGPUreadbackindependentlyverifiesit. Finalengine-liquid-foam-optics-v2:
10cleanpasses0warnings/failures22.899s,session95610terminal0.
LatestNS/map/uprojectSHA256unchangedfrompreviouscheckpoint.

Nextphysicalvisualwork: coherentfree-surfacereconstruction, distinguishsubmerged
shear/aerationfromtopfoamandconstrainfoamtransporttosurface. Primaryauthor
overviewhttps://alexey.stomakhin.com/research/whitewater.html separatesbubbles
andmanifold-advectionfoam; currentcodeNOTthatSPH/coupledsimulation. Fullpaper
fetchfailed26MB; donotclaimread. Native/3Dlateralhandoff/storage,fullscene
integration,performance,photographiccomparisonandalllaterqueueitemsremainopen.

## September 8 — anisotropic reference, not renderer promotion

Actual GPU particle reconstruction processes76750,14828,21299 all terminal0.
No UE/build process launched this segment. New Python-only reference, tests and
nested-grid comparison documented in liquid-anisotropic-reconstruction.md.
Primary Yu/Turk2010 PDF downloaded and visually read; weighted covariance,
render-only center shift, cubic density SUM, not ellipsoid union or SDF.
Initial nominal weights retained. Corrected equal-mass/inverse-local-number-
density weights reduce clustering dependence; duplicate sampling test passes.
Added finite coincident-neighborhood fallback and exact affine crossing test.
54 focused liquid Python tests PASS1.453s. No new engine test/build claimed.

Actual80,629particles: coarse normalized iso0.5volume317.27m3; double-resolution
318.94m3. Density integral refined441.93 vs kernel441.76m3, NOT calibrated
physical volume. Highest-crossing RMS refinement difference8.02cm,max1.18m;
detached droplets not separated.40.6%coarse kernels subvoxel,4.1%fine.
No real renderer integration/performance/visual acceptance; no source particles
moved, no production resolution changed, no saved engine assets touched.

Next: coherent main-body/crest and temporal reconstruction validation; density
must become distance-correct surface before SDF raymarch. Keep bounded GPU cost.
Then actual engine motion/foam, native exchange/storage, full scene integration
and photographic gates. Entire goal and later queue remain active, no commit.

### Same segment — controlled crest and main-body checks

Added audit_liquid_reconstruction_features.py:19,200 deterministic particles,
known1.5m surface,0.2m amplitude/3m wavelength, plus1/30m translation on0.1mgrid.
Initial center averaging lowers flat17.37cm/crest18.16cm: REJECTED forpromotion.
Unshifted covariance centers preserve flatlevel to+2.04cm, crestamplitude20.19cm
(translated20.29cm), crestlevelbias+1.84/+1.86cm. Isotropicbaselineflat+3.42cm,
crestamplitude19.47cm. Controlledtests are NOT actualengine orvisualacceptance.
Evidence liquid-anisotropic-controlled-features[-unshifted]. Sessions71105,
98328 terminal0. AddedCLI --smoothing0; doesnotchangephysicsorsavedassets.

Actualunshifted80,629particles coarse/refined sessions38677/76104terminal0.
Evidence liquid-anisotropic-unshifted-60s[-refined]. Iso-volume382.10/389.87m3,
notphysicalbudget. compare_liquid_surface_reconstruction.py nowseparates
6connectedcomponents in diagnosticcopiesonly:352/186components; mainbody
heightrefinementRMS11.91cm,p9525.01cm,max1.36m. Shiftedcandidate mainbodyRMS8.42cm.
Detached droplets doNOTexplain instabilityaway. No sourceparticledeletion.
56focusedPythonliquidtestsPASS1.371s. NoUE/buildprocesslive,lastcheckednone.
No commit,promotion,goalclosure. All owned CPU processes terminal0.
Nextresolution-awarekernelfootprint/reference validation, distance-correct
boundedcostGPUintegration then actualmotion. Fullqueueunchangedactive.

## September 8 late — prefilter, metric distance and exact-source engine A/B

PROGRESS: new resolution-aware reference and real-engine rendering of its SDF.
Full details in liquid-surface-snapshot.md. No production promotion/commit.

filter_kernels adds voxel-box second moment to normalized cubic covariance
(.075 per-axis); new axes sqrt(axis²+footprint²/.9). Centers/weights unchanged.
Approximation, NOT exact box convolution or calibrated isovolume conservation.
Actual80,629particles radius.4m,unshifted,footprint1/6m. Coarse/refined artifacts
liquid-anisotropic-prefiltered-60s[-refined], sessions73505/30943 terminal0.
Main-body refinementRMS8.29cm,p9516.26cm;stillnotconverged. Controlledfeatures
prefiltered session19241terminal0:20cmcrest->20.156cm, translated20.137cm;
flatbias+1.94cm,crest+2.24cm.63focusedtestsnowpass (latest1.621s).

liquid_density_surface.py: consistent6tets/cube surface, exact point-triangle
distance truncated.5m, densitysign.749,448triangles;183.49sOFFLINE,NOTrealtime.
Process43836terminal0. Artifactsliquid-anisotropic-prefiltered-60s-surface:
surface.npz,surface.rgba16f(R=cm,GBA0),report.json. Conversion topcrossing
RMS8.78mm,p9518.26mm. Hugeinterfacecountmotivatesbulkvoid/physicsmaskaudit.

NewC++ RaftSimEditorLiquidSurfaceSnapshot.cpp command:
RaftSim.LiquidSurfaceSnapshotReview source-dir new-report-dir
Restrictsdocsroot,domain136x136x48,finiteR[-50,50]cm,GBA0,onefrozentransientFoam
component/MID. UnsavedUVolumeTexturePF_FloatRGBA bilinearclamp; actualGPUupload
readbackbyteexact all887808voxels beforebindingVolumeTex. NoSimRT/simwrite.
Fixtureparticles diagnosticsnowrecordmaterialtextureparameters.
capture_south_fork_liquid_terrain.py flags -RaftSimLiquidSurfaceSnapshot=DIR
and optional -RaftSimLiquidSurfaceBaseline=DIR requirefoamoptics,fixedoblique,
steps3600. Freezeoptics2cases,same.001scattering/.12roughness/exposure-10,foam0.
Firstcapture liquid-surface-snapshot-engine session29552terminal0,88.706s:
newruntimebaselinevspriorsnapshot NOT strictsameparticleA/B,retainedintegration.

PreparedoriginalcapturedSDFbaseline fromprior60svolume_00.rgba16f preservingR
bitexact; geometry_only_volume clearsGBA only. Newprepare_liquid_surface_baseline.py.
Outputliquid-original-60s-surface textureSHA0dfbc0113ebc64cac8aae1c8f1c0969304ad8bcd83d8b18bfb5c0bc72fc2fc68.
ReconstructedtextureSHA4ac535ad2fd9df8f2f94662d2795c81759fe6ecd542c1661be83ba4151cc9d8c.
BothparticlecaptureSHA4fa693dc140af6f757194b57ffbad06f83d847eaf6d13e278d5c7d6d5c9920ce.
Exact-sourcecapture liquid-surface-snapshot-exact-source session64157terminal0,
88.945s. Bothbindings GPUbyteexact; optics00/01actualMIDVolumeTex_0/_1,all
scalar/vectoruniformsequal. audit_liquid_surface_snapshot.py verifiesgeometryA/B
includinghashes/controls/currentbindings;114462pixelschange>2levels. Bothimages
viewed: finerbreakupbutstillplastic/cyan,rectangularwindowwalls,rawangularbed.
Nofoam/liveanimation/performance/photorealacceptance. DoNOTcallofflineGPUupload
the liveGPUreconstruction. Needactualper-framealgorithmnext.

Build26625PASS27.99s;baselineextensionbuild14868PASS12.40s.
Engine10regressions engine-liquid-surface-snapshot/index.json PASS0warnings/
fails23.738s(session57617terminal0),beforeminimalbaselinekindextension.
Exact-sourcecaptureexercisedlatestextension. NoUE/build/CPUprocessleftlive.
SavedNS/map/uprojectSHAunchangedaspriorcheckpoint. GPUtestsurveyreportsAMD
RadeonbutactualD3D12logselectsadapter0RTX3060Laptop5994MB;donotchangeselection.

Next audit actualfluid/airclassifiedinterior versus reconstructedinternalvoids,
then bounded-costliveGPUreconstruction and surface-consistentaeration. Notmore
unmeasuredwave/whitemultipliers. Native/3Dexchange/storage,fullscenecarrier,
shoreline,motion/performance/photoacceptance andentirelaterqueue stillopen.

## Continuation — GPU distance reconstruction and occupancy consistency

See [GPU reconstruction review](liquid-gpu-reconstruction-review.md) for this
pass's consolidated evidence and explicit limitations. Do not repeat the completed
snapshot A/B as a substitute for live integration.

- New `liquid_surface_occupancy.py` reconciles density with conservative 27-cell
  solver-fluid interior confidence. Actual core-air samples decrease from 26,135
  to 209, with no added liquid in nonfluid parent cells. This changes exposed
  heights too (13.75 cm RMS, 1.69 m max); not an accepted mass/shape correction.
- New `liquid_eikonal_surface.py` provides the metric CPU reference. Twelve
  iterations converge on the captured field; comparison with exact triangle
  distance has 3.10 cm RMS error. Approximate ray-march distance, not exact SDF.
- New `RaftSimLiquidRedistanceGPU` and shader implement actual render-graph
  seed/iteration/resolve passes. Diagnostic viewer binds the computed output
  after independently checked readback. Anisotropic density and occupancy input
  remain offline; no live Niagara hookup exists yet.
- `liquid-occupancy-eikonal-gpu-engine` and `...-timing` both complete. The GPU
  output matches CPU sign and distance within 0.03125 cm maximum; independent
  audit verifies saved bytes, source identity and identical optics. The original
  control decoded image is unchanged from the earlier exact-source run. Actual
  candidate inspected: fewer internal gaps, still plastic rounded water and
  rectangular diagnostic boundaries. Foam is zero for this comparison.
- Eight hardware timestamp intervals measure 3.739–3.778 ms for reconstruction
  only. This excludes simulation and scene rendering, and predates the small
  explicit half-rounding correction below. Capture wall time is not FPS.
- New changing-input GPU regression checks three metric planes, empty/full
  volumes, alias rejection and exact half coverage preservation. Initial run
  `engine-liquid-gpu-redistance` fails coverage; diagnostic `...-coverage` shows
  downward half conversion. Explicit nearest-even selection before typed UAV
  storage fixes it without weakening the assertion. `...-final/index.json`:
  11 passes, zero warnings/fails, 23.05 s. All 73 Python liquid tests pass.
- Builds: initial session 8585 succeeded 1,420.76 s / 103 actions; timestamp
  43873 succeeded 14.65 s; regression 93196 succeeded 14.99 s; diagnostics
  4898 succeeded 15.30 s. Shader-only rounding fix compiled in final engine run.
- Captures 76364/31141, tests 15902/5369/21984 all terminal. No owned editor,
  build or solver is left running. Saved review NS, map and uproject hashes
  remain unchanged. No commits or pushes; the complete project goal stays active.

Next: generate the current scalar/occupancy field on GPU and hook this component
to the live renderer with correct update ordering and surface-consistent foam.
Then assess actual animated shape, performance and whole-scene shore continuity.
Native/3D exchange/storage acceptance and all later queued scenes remain open.

## September 9 — actual live GPU density pipeline

Previous goal turn classified as progress; this continuation also advances
authoritative code and actual live-engine evidence. Full goal remains active.

New GPU module files: `RaftSimLiquidDensityGPU.h/.cpp` and
`RaftSimLiquidDensity.usf`. Four reconstruction passes implement binning,
weighted covariance/eigenbasis fitting, normalized unshifted cubic ellipsoids,
prefiltering, fixed-point splatting and scalar output. A fifth pass packs actual
Niagara planar float positions and its live GPU count. The generic interface
accepts an RDG graph and does no CPU readback/upload. Includes kernel-support
halo and four failure counters. Source max allocation 262,144, max voxels 2M.

`prepare_liquid_gpu_particles.py` prepares the existing 80,629-particle captured
reference (SHA `4fa693dc140af6f757194b57ffbad06f83d847eaf6d13e278d5c7d6d5c9920ce`).
`RaftSim.LiquidDensityGPUReview` in the snapshot viewer computes and exports
kernels, fixed density and lossless R32f scalar. The Python launcher
`review_liquid_gpu_density.py` checks input identity and exits the editor.
`audit_liquid_gpu_density.py` independently verifies every quantity.

Passing `liquid-gpu-density-r32/parity.json`: density max error 0.00002902,
matrix max error 0.00002716/m, weight max relative error 0.00000793, all 14,859
top columns preserved, max top difference 0.02081 mm, raw R32f scalar exact,
all diagnostics zero. First shader launch failed Unreal root-parameter parsing
(multiple bound declarations per line); separate declarations fixed it. The next
run failed only its lossy R32f-to-half diagnostic readback; original float32 copy
fixed it without changing gates. Both failures retained. One-shot GPU intervals
including diagnostic copies differ (9.428 / 23.785 ms); not stable timing/FPS.

`RaftSimEditorLiquidLiveDensity.cpp` implements start/stop commands for the
unsaved origin-tile terrain fixture. Uses Niagara's post-simulation render-graph
event, current full-precision particle buffer and live GPU count. Runs density
then the new RDG overload of redistancing. Copies the result into the existing
visible SimRT red channel, preserving its green coverage. No second mesh,
no solver-grid or particle-state writes, no per-frame CPU readback. Stop removes
the callback and performs a blocking export; world cleanup removes it before
simulation destruction. The script flag is `-RaftSimLiquidLiveDensity`, requires
foam optics/fixed oblique/foam motion, excludes offline snapshots. Starts at
step6, exports at finish.

First live capture (`liquid-live-density-12s`) had a render-graph external-access
ensure despite completing. Its independent audit explicitly fails. Fix:
resume internal texture tracking before CopyDest, restore external SRV access
afterward. The corrected `liquid-live-density-access-12s` passes independent
audit: 750 updates, 71,016 final particles; packed/current-cache positional max
error 0.001504 mm; finite R[-50,50] cm and G[0,1]; all diagnostics zero; 30/30
distinct motion frames; zero engine error lines. Capture wall39.54s is not FPS.
Viewed first/last motion images: moving relief, still cyan/plastic and exposed
rectangular window walls. Not accepted whitewater. Occupancy reconciliation is
still CPU-only and absent from this live pipeline.

Tests: 75 Python liquid checks pass (2.736s); engine-liquid-live-density-final
11 passes, zero warnings/fails (23.91s), after the live bridge/RDG refactor.
The final coverage-source alias/domain guard build passes7.83s; the final focused
distance regression passes (one test, zero warnings/failures, 0.0282s) in
`engine-liquid-live-density-guards-final/index.json`. Compilation fixes retained in output history:
global Cleanup name collision and reference-vs-pointer GetParticleData API.
The successful live bridge build was81793 (15.52s), access fix7501 (14.16s).

All capture/build/test handles are terminal; no UnrealEditor or ShaderCompileWorker
processes remain at the final check. The
completed old density diagnostic34716 ignored console quit; exact command-line
identity was verified and only that owned process stopped. The Python launcher
and both live captures subsequently exited cleanly. Saved NS/map/uproject SHA
values remain unchanged. No commits/pushes; no production promotion.

Next: coherent bulk/foam treatment on the live field (not merely increasing a
white multiplier), uninterrupted GPU/frame-cost profiling, and reference-based
animation/optics calibration. Then whole-scene shoreline/carrier/raft integration
and hydraulic acceptance. Do not redo the completed frozen snapshot milestone.
South Fork is not accepted; Colorado, Pacuare, Futaleufu and the complete broader
queue remain open in their original order.

## September 9 — uninterrupted live reconstruction cost

Prior turn: PROGRESS, final focused distance guard regression verified and
recorded. This turn: PROGRESS, actual uninterrupted native/live cost comparison
and nonblocking GPU stage timings. Full goal/queue remains active; no promotion.

Added `-RaftSimLiquidTerrainBenchmark` to the existing transient capture script.
Frames240–720 are 480 timed callbacks, with no PNG/particle/grid reads inside
the interval; the same960×640 scene is rendered each frame. Real simulation
advances1/60s per callback. Added optional `start profile` to the live density
bridge:16 query slots,4 timestamps each, nonblocking polls, no slot reuse before
results, first240 GPU updates excluded by the independent audit. Timestamp
window is explicitly not claimed to match the Python window exactly.

Initial build34403PASS46.99s. First run13877terminal1:
`liquid-live-benchmark-12s` crashes on shutdown because pooled query destructors
assert render-thread ownership even when empty. Retain failure; report alone is
not acceptance. Query storage is now a TArray constructed and destroyed on RT,
along with its pool, before the shared state returns to GT. Corrected build
34588PASS18.25s; corrected live run16782terminal0; native run96454terminal0.

`liquid-live-benchmark-owned-12s/benchmark_audit.json`:480 positive intervals,
mean23.315ms,p9525.348ms,max33.983ms;715 GPUupdates,471postwarmup samples;
GPU packing+density mean5.365ms,distance.577ms,copy.0239ms,total5.966ms,
p95total6.467ms. All queriesordered, stage sums consistent, zero skips and
diagnostic errors. No engine errors, clean exit. No blocking timing wait.
`liquid-native-benchmark-12s/benchmark_audit.json`:480intervals,mean16.773ms,
p9518.430ms,max31.956ms, no engineerrors,cleanexit. Difference6.542msmean is
consistent with measured reconstruction cost. NOT packagedFPS, release target
or stable multisession distribution; runtime caps/thermal state unrecorded.

Viewed final images from native and reconstructed runs. Both remain cyan,
plastic, weakly frothy and have exposed rectangular fixture sides. More surface
detail alone is not whitewater. Keep reconstruction out of production.

Added independent timing audit +3 rejection/metric tests. All78liquidPython
testsPASS2.783s. Engine suite48954terminal0:11passes,0warnings/fails23.18s in
`engine-liquid-benchmark-final/index.json`. Saved NS/map/uproject SHA unchanged.
Full evidence: `liquid-live-performance-review.md`. No commit/push.

Next advance live solver-occupancy support and foam coherence, with GPU parity
to the existing CPU occupancy reference. Then real-reference optics/motion and
repeat timing. Density gathering is the actual measured cost center. Do not
repeat frozen snapshots or claim the benchmark is full-scene acceptance.

## September 9 — live GPU solver-fluid interior support

Prior turn PROGRESS: uninterrupted native/live benchmark and actual stagecosts.
This turn PROGRESS: added `RaftSimLiquidOccupancyGPU` and connected it to actual
current solver classification in the live reconstruction, behind
`-RaftSimLiquidLiveBulk`. Full objective/queue remains active, not narrowed.

New shader/implementation: `RaftSimLiquidOccupancy.usf`,
`RaftSimLiquidOccupancyGPU.cpp`, public API in `RaftSimLiquidDensityGPU.h`.
Two stages: full27-neighbor fluid erosion; cell-centered trilinear support and
phi=min(raw_phi,.5-support). Current68×68×24RGBA classification is resolved by
systemID/name/type/layout, currentRT texture passed directly, noCPUupload or
perframe readback. Uniform1×/2×/4×refinement only; invalid categorical values,
badsourcephi and newwetnonfluidparent diagnosed. Correctedscalar feeds actual
distance and existingSimRT; no solver/particle/boat mutation orsecondmesh.
Stop exports rawdensityfixed, correctedphi/support(float2), currentboundary and
surface for independent audit. Audit buffer is diagnostic overhead, not optimized
production code. Saved assets remain unchanged.

Build39132PASS25.50s. Live motion76410terminal0 in
`liquid-live-occupancy-12s`:750updates,71036particles,all4diagnostics0,
noengineerrors,30distinctmotionimages. Independent occupancy audit: boundary
exactlymatches separate nativegrids, phimaxerror4.768371582e-7,
confidencemaxerror4.768371582e-7,13740falseair fullysupported samples→0,
23067newwetsamples,0newwetnonfluidparent,0renderedsignmismatches. Gates were
predeclared2e-6phi/1e-6confidence,zerooutsidewater; notloosened. Particlepacking
maxerror.001595mm. Wall40.395s includesdiagnostics,notFPS. Viewedmotion029:
stillcyan/plastic/weakfoam/rectangularfixturesides,notphotorealacceptance.

New independent `audit_liquid_live_occupancy.py` +3Python tests. Initialtinytest
fixture had no fullysupported2×2×2core duecentralobstacle; enlargedthefixture
withoutchangingthealgorithm/assertion. All81liquidPythonPASS2.669s.
Added actualGPUregression `RaftSimEditorLiquidOccupancyTest.cpp`:uniform1/2/4,
mixedclassifications,emptyair,invalidinteger/fractionalcategory,baddomain and
nonewwetnonfluidparent. Build87438PASS15.10s. Fullengine37254terminal0:
12successes,0failures25.13s in`engine-liquid-occupancy-final/index.json`.
One warning in oldTerrainGridFrameTransfer: LogHttp google/generate_204 timeout;
newoccupancytestwarningfree. Addedexplicitfiniteassertion,finalbuild30690
PASS9.64s; focusedfinaltest84130terminal0:1pass,0warnings/failures,.03s in
`engine-liquid-occupancy-finite-final/index.json`. No UnrealEditor or shader
compiler processes remain at finalcheck.

Benchmark89448terminal0 in`liquid-occupancy-benchmark-12s`:480intervals,
mean23.063ms,p9525.377ms;471warmedGPU totalmean6.009ms,
pack+density+occupancy5.410ms,distance.575ms,copy.0237ms. Labelpack_density_ms
includesoccupancy (source report flagrecordsit). Compared withprevious5.966ms,
no evidentlargecostregression; doNOTclaimpreciseisolatedcost/speedup or gameFPS.
Finalbenchmarkoccupancyauditpasses:13598falseinteriorair→0,0newwetnonfluid,
sameCPUerrors4.768e-7,0signmismatch,nativeboundaryexact. Allcapturescomplete.
SavedNS/map/uproject SHAvalues unchanged. No commits/promotions.

Next: livefoam on corrected current surface, not merely a white multiplier.
`RaftSimLiquidFoam.h` currentlyevolvesGaroundoldnativeSDF beforepostrender
reconstruction; optics samplesGatnewhit. Needpersistentcurrent-surfacefoam
history,velocityadvection/decay,sourceplacement and pause stability. Do not
evolvefoam duringextra render-onlycallbacks. Engine context offers
`bHasTickedThisFrame_RT`, but ReleaseTicks resetsit; check actualeventordering
beforeusingasstepidentity. Currentpostrendercallback runs750timesvs720simsteps.
Then referenceoptics/motion andwhole-scene shore/carrier/raft/physicsacceptance.
Fullreview:`liquid-live-occupancy-review.md`. Later rivers/crew/cleanup stillopen.

## September 9 heartbeat — simulation clock prerequisite for coherent foam

No UE/build process was live at entry. First unfinished river is still South
Fork; no new cook or other river was started. Bounded progress: instrumented
the live bridge with read-only simulation-tick/render-only callback counters,
then verified them in `liquid-live-step-clock-12s`. This resolves the pending
question about blindly treating each render callback as one fluid step.

Engine source: NiagaraGpuComputeDispatch.cpp registers FinishDispatches as a
graph post-execute callback, then broadcasts OnPostRenderEvent during graph
construction (near lines2216–2256). FinishDispatches calls ReleaseTicks, which
clears bHasTickedThisFrame_RT. Thus that flag can be inspected in the existing
post-render graph-building hook, before cleanup. It is only a boolean, not an
elapsed-time or substep counter. BufferSwapsThisFrame_RT also increments on
particle-writing simulation stages and must not be substituted for time.

Build32704PASS18.39s. Runtime48329terminal0; noengineerrors. Actual report:
750 reconstruction callbacks,709 with the simulation-tick flag,41 render-only.
Do not evolve foam for750*(1/60)s; do not assume709flags account for the nominal
714 post-install steps either. Per-system actual age/delta accounting (including
batched ticks and reset) is required before implementing foam evolution.
The new fields are diagnostic only and do not change reconstruction or physics.

Existing independent live/occupancy audits pass on this run:71084particles,
position maxerror1.536e-6m,30distinctmotionimages,750updates,all4diagnostics0;
boundaryexact,phi/supportmaxerror4.768e-7,13940falseairinteriors→0,
0newwetnonfluid,0displayedsignmismatch. No new visual acceptance claimed.
No active UE/shader processes at finalcheck. No commit/push/promotion.
Next remains current-surface foam with a verified simulation clock, followed
by physical/reference/whole-scene acceptance. Full queue/goal unchanged.

## September 9 14:09 heartbeat — actual GPU simulation-age clock

Entry process check found no UE/build work; South Fork still first unfinished.
Previous heartbeat PROGRESS: callback/tick flag probe. This heartbeat PROGRESS:
actual GPU-carried age with verified integrated elapsed time and pause handling,
not another callback-count approximation. Full goal/river order unchanged.

The GPU system proxy's PendingTicks is private; no engine/private-memory hack
was introduced. Instead the transient foam graph now writes Emitter.Age to
SimRT.B/A, whole seconds + fraction. `RaftSimRecordLiquidClockGPU` reads this
current texture into a persistent4096-recordGPUtimeline: age, elapsedDelta,
resetFlag,diagnosticTickFlag. Stop-only readback. Normal optics remain fromR;
distance now preservesGBA and its actualGPUtest checks nonzero varyingB/A.
No particle/solver/boat mutation or new visible surface. New diagnostic clock
timeline requires stop before4096updates, consistent with bounded60s capture.

First build command had a duplicated project path and exited before building;
corrected build51061PASS48.45s. First GPUage run21800terminal0:
`liquid-gpu-age-clock-12s` fails predeclared .00025s clockgate despitecleanexit:
final11.999511719 vs independent11.999989, error.000477281s. Native half-float
typedUAV truncates arbitrary fractional age. Retainedfailure; notaccepted.
Fixedfractionencoding=round(frac*2048)/2048 beforehalfstore, exactlyrepresentable
binaryvalues; maxageerror1/4096s inboundedrange. Gateunchanged. Build75159
PASS20.11s. NewCPUtestchecks200001ages0–70s forhalfexactstorage/errorbound.

Correctedrun17038terminal0 `liquid-gpu-age-quantized-12s`:
clockauditPASS750records, first.10009765625s,last12s, independent11.999989s,
finalerror.000011s, sumdelta11.89990234375s exactlylast-first;709positivedeltas,
41render-onlyrecords,maxdelta.033203125s (batchedelapsedtime accounted for),
last32callbacksageconstant/delta0, displayedB+Aexact,resetrecords0,noerrors.
Actual reset behavior remains to test before foam history uses resetflag.
ClocksourceSHAef7c50bd539998661628d89f3252ae568875827bcea60fa553a35b25bb491828.

Independentlivepipeline/occupancyauditsalsoPASS:71045particles,packingmax
1.4881e-6m,30distinctmotionimages,0diagnostics,exactnativeboundary,
13952falseairinteriors→0,0newwetnonfluid,0signmismatch,phi/supportmax4.768e-7.
Wall47.412sincludesblockingdiagnostics,notFPS. Viewedfirstagecandidate's final
motionimage: samecyan/plasticweakfoamrectangularfixture;no visualacceptance.

All85liquidPythonPASS2.556s. Fullengine60150terminal0:
12successes,0failures32.80s in`engine-liquid-gpu-clock-final/index.json`;
oneunrelatedLogHttp google/generate_204timeoutwarning inCollisionConfiguration.
Distance metadata regression itself passes. NoUE/shaderprocessesremain.
SavedNS/map/uproject SHAunchanged. No commits/promotions/newcooks.

Next implement current-reconstructed-surface foam evolution, persistenthistory,
velocityadvection/decay usingGPUage delta; preserveonzeroDelta,clearactualreset.
ExistingfoamstillderivesfromnativeSDF; clockisnowavailablebutfoamevolutionnotyet
implemented. Do not repeat completedclockprobes. Reference/whole-scene/physics
andlaterqueueitemsstillopen. Review:`liquid-gpu-clock-review.md`.

## September 9 — current-surface foam transport implemented and verified

Previous goal work made progress: new persistent RK2 GPU foam uses the current
reconstructed distance and actual current velocity, with GPU simulation delta,
decay/source, zero-delta identity and reset initialization. Existing SimRT is
still the only visible surface. No production promotion or solver mutation.
New API/shader: RaftSimLiquidFoamGPU.h/.cpp, RaftSimLiquidFoam.usf; half rounding
helper shared with distance in RaftSimLiquidHalf.ush. Live bridge supports
`start [profile] [bulk] [foam]` and nonstopping `inspect OUTPUT`.

Retained initial active audit failure in `liquid-current-surface-foam-12s`:
float rounding included exactly 50 cm support edge, max coverage error .16235.
Support cutoff now explicitly half-representable, with GPU/CPU regression.
Audit compares XYZ velocity rather than its padded fourth channel. No loosened
tolerances. `liquid-current-foam-cutoff-12s` passes active and paused independent
transport: max coverage .000732422, source .000769272/s, advection .000624164.
Paused history/RBA exact; velocity/boundary match independent grid readback.
Live/clock/occupancy audits also pass, 70963 particles, 750 updates, 30 distinct
motion images. Build57796PASS13.68s; engine58063terminal0: 13 successes, no
failures/warnings (`engine-liquid-current-foam-cutoff`). 90 numerical tests pass.

Benchmark2535terminal0 (`liquid-current-foam-benchmark`): independent audit
verifies 480 uninterrupted editor-fixture intervals, mean22.6605ms/p95 25.1525ms;
471 GPU samples total6.1731ms, density5.4838ms, distance.5774ms, foam+copy.11194ms.
Not packaged-game FPS. Actual images still cyan/plastic and weakly frothy with
rectangular test edges. This is not physical/photoreal/whole-scene acceptance.
See `liquid-current-surface-foam-review.md`. Saved NS/map/project unchanged by
these transient tests. Full South Fork and later queue still incomplete.

The optical control run above has finished; it did not fix the appearance.
See the September 9 secondary update below for the current next action.

## September 9 — secondary emitter integration, still visually incomplete

Previous user-status turn was informational only; the resumed goal turn made
code changes and gathered new actual GPU evidence. No outstanding UE/build
process remains: sessions 54194,33510,49787,13641,95722,56256,47645 and their
builds are terminal. Revalidate before the next launch.

Added clock-only `surface-foam` construction so the native SDF grid never gets
the redundant RiverFoam attribute. This fixes the secondary RGBA reader mismatch
without globally changing grid formats. Enable secondary before primary optics
installation; installer selects only the primary material. Native spawn request
now matches its 2048 safety ceiling; previously Niagara discarded the entire
10000 request. Telemetry preserves primary contact assertions but separately
records secondary UniqueID/position/velocity with source ID -1.

Authoritative full capture: `liquid-secondary-particle-records-12s`, terminal0,
completeTrue, zero errors/rejected spawn batches,750 updates/30 distinct motion
frames. Live and current-foam audits pass; active coverage max error .00048828125,
paused history exact. Actual secondary counts at6/30/60/240/480/720:
0/1/1/1/0/0. One tracked particle moves64.98cm in.5s. Corrected secondary audit
is `secondary_audit_v2.json`; no terrain/visual/performance acceptance.

Latest engine run `engine-liquid-secondary-budget`:12 clean successes,1 success
with unrelated Google connectivity timeout warning,0 failures,13 total. It
tests the compiled2048 request and single secondary renderer.95 numerical liquid
tests pass. Latest build73731succeeded16.02s; scoped diff whitespace check clean.
Saved contact NS, review map, and uproject SHA256 still match prior checkpoint.
No production promotion, commit, push, or scene completion.

Next required implementation: native secondary source has an actual compiled
curl typo (Vy_left reads X+1), scalar metric for all axes, and no SimDt factor in
emission probability. Thresholds actually compiled are5..20/s, unlike stock
template600..1000. Actual near-surface metric curl median.622/s,p99 4.014/s;
only32/15704cells above5/s. Do not blindly tune from template defaults. Correct
source/time/coordinate math, connect spray to current reconstructed surface,
then inspect motion/terrain/cost and visible froth. Image remains glossycyan
with rectangular fixture edges. Full SouthFork and later queue remain active.
