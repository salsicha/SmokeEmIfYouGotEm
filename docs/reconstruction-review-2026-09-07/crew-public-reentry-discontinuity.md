# Public reentry discontinuity — September25

Actual D3D12 editor-world production-raft regression now exercises successful
`RequestSelectedReentry`, rather than testing only its `RemoveSwimmerAt` helper.
The existing rotated raft, real rendered hull, crew avatars, integrator and
occupancy assertions remain. This is a native fixture, not normal-play video.

The test establishes ReadyForReentry explicitly; it does not claim to validate
the preceding user-input, thrown-line or pulling sequence. It computes the tube
target after setting the current reentry pose, then invokes the public request.

- Exact current hull distance:1.140148845m, within unchanged1.35m gate.
- Root displacement during the synchronous request:392.377744591cm.
- Elapsed simulation time during that displacement:0seconds.
- Avatar identity preserved; swimmer removed; rescue count increments once.
- Repeating the request does not board another swimmer or increment the count.
- Occupied crew mass235→310kg and integrated raft mass455→530kg, with the existing
  impulse/inertia checks passing. Other original occupancy cases also pass.

This proves a discontinuity for this fixture, not a universal3.92m jump or a
body/raft penetration measurement. `AttachAvatarToSeat` immediately selects
SeatedIdle and relocates the root; no elapsed-time boarding traversal exists on
this path. The Reentry pose alone is not a climb animation.

Initial fixture incorrectly reused a tube target calculated before later raft
and pose changes. Boarding was refused, and downstream assertions failed.
Preserved failed report: `tmp/crew-public-reentry-20260925/index.json`. It is not
evidence of a broken readiness gate. Correcting current-state setup, without
changing the gameplay gate, yields1success/0failures/0warnings/0not-run, engine0:
`tmp/crew-public-reentry-v2-20260925/index.json`. Full measurement log:
`tmp/crew-public-reentry-v2-20260925.log`. Editor builds29.52s and11.11s passed.

Next repair needs an elapsed-time boarding state and coordinated root/body/PPE
motion over the actual tube, followed by seated ownership. Preserve readiness,
distance, duplicate-request, occupancy and rescue-count protections; validate
when mass transfers and when paddling becomes available. A straight interpolation
from this target to its assigned seat could cross the hull and must not be called
a collision-safe climb. Review actual continuous rendered motion, each identity,
both sides, tilted/moving raft and interruptions/checkpoint resets.

No runtime behavior, saved asset, packaged executable or river acceptance changed.
The passing occupancy regression is explicitly not reentry-animation acceptance.

## Ready-pose ownership repair

The next production pass found `DriftSwimmers` unconditionally applying Swimming
before its hull-clearance query and again after positioning. The later rescue
update restored Reentry for the selected ready passenger. This repeatedly changed
pose ownership and reset animation phase inside each frame. Drift now selects
Reentry only for the matching ReadyForReentry target; all other swimmers retain
Swimming. The same selected pose is used for clearance and the final update.
No readiness/distance limit, hull clearance, mass or completion rule changed.

Before the runtime fix, the extended native test fails exactly eight ready-pose
assertions (`tmp/crew-ready-pose-before-20260925/index.json`). Afterward the same
test passes (`tmp/crew-ready-pose-after-20260925/index.json`). Additional checks
pass12elapsed updates at1/60s with finite body and PFD error<0.01cm, unoccupied
crew mass235kg while waiting, another passenger still swimming, and release to
Swimming when the target's phase returns to Pulling. Eight zero-step cycles
retain the ready root within0.01cm. Final D3D12 report:
`tmp/crew-ready-pose-elapsed-20260925/index.json`,1success/0failures/0warnings/
0not-run, exit0. Tests exercise production methods directly in an editor world,
not human input or an inspected continuous gameplay animation.

Editor builds11.03s (new failing regression),29.72s (runtime fix),11.03s
(elapsed checks) succeed. The ordinary Boot/menu South Fork launch exits0 with
raft speed1.367m/s,wet1,support delta0 and sampled penetration0. Separate300frame
CSV rows30–270 give mean21.763666ms,p9530.2152ms. Nonlegacy timing is confirmed
in `tmp/crew-ready-pose-normal-20260925.log`; report with CSV SHA256:
`tmp/crew-ready-pose-normal-cost-20260925.json`. This no-rescue run is a launch
regression check, not direct rescue validation or a performance improvement claim.

The392.377744591cm instantaneous boarding jump still exists and is still logged.
This fixes a competing pose owner required before a timed climb, not the climb
itself. No cap geometry, flow field, saved map, packaged stage or remote changed.

Standalone Development game target also rebuilds successfully in119.34s. Its
binary is not yet restaged or separately packaged-play qualified. The normal
editor-hosted game test above used the rebuilt production runtime without opt-in.

## Timed boarding candidate: visual rejection

The subsequent uncommitted candidate is gated by `-RaftSimTimedReentryReview`.
It keeps the passenger detached and unoccupied until completion, interpolates
the published body/PFD pose, and follows the raft-local transform. It is NOT
enabled in ordinary play. Editor builds succeeded, but no standalone rebuild or
packaged acceptance is claimed for this candidate.

Native D3D12 receipt `tmp/crew-timed-reentry-v2-20260925/index.json` reports
1 success, 0 failures and 0 warnings. The move spans 236 updates (3.933333333s),
392.377744591cm total root displacement and 2.572115456cm maximum sampled step.
Occupancy, duplicate request, finite pose and PFD checks pass in this fixture.
The v1 log's zero elapsed label was erroneous; v2 logs simulated elapsed time.

Actual engine keyposes are retained locally in
`tmp/crew-timed-reentry-views-20260925/frame_*.png`, not added to Git. At frame120
the passenger visibly floats above the raft with hands unanchored. The authored
60cm sine-squared lift and interpolated pose therefore fail visual climb review,
despite smooth numerical motion. Do not promote this trajectory or rerun it
unchanged as an acceptance attempt. These dark geometry views are not a lighting
review, a continuous motion review, or collision/contact qualification.

Next work must establish a tube-contact hand/body path before seat transfer,
then test interruptions, successful/rejected checkpoint restore, moving/tilted
rafts and both boarding sides. Cancellation and checkpoint hooks exist in the
candidate but are not yet regression-qualified. No river geometry, cooked field,
normal playable boarding behavior or release acceptance is changed by this review.

Follow-up without the experimental switch:
`tmp/crew-timed-reentry-default-20260925/index.json` reports 1 success,
0 warnings, 0 failures and 0 not-run; engine exit0. This checks the existing
native default occupancy path, not a new normal-game visual/performance run.

### Hand-support measurement

The subsequent fixture measures published hand pose controls against the exact
visible hull triangles (not bounding-box distance). This is control-point
distance, not proof of rendered skin contact, a stable grip or support forces.
`tmp/crew-boarding-hand-support-20260925/index.json` completes with engine exit0;
the added test module builds in11.40s. Frame0 left/right gaps are
101.862194847/137.533406722cm; frame120 gaps are119.278552440/117.416237470cm.
The maximum nearest-hand gap is119.875484632cm. Both hands exceed10cm for217
of236 sampled poses (initial pose plus235 pre-completion updates). The10cm
counter is diagnostic, not a newly accepted contact tolerance.

Thus the problem starts before the authored lift: the conservative whole-body
pull envelope is not a reachable handhold. A reach/approach/contact stage must
be resolved against rendered geometry before a supported pull-over and seat
transfer. Removing only the sine arc does not establish such a climb.

### Cancellation ownership repair (review-only controller)

The new interruption regression reproduces two failures before the fix:
the next rescue update reapplies Reentry, and another request restarts boarding
without a new rescue interaction. Receipt:
`tmp/crew-boarding-cancel-before-20260925/index.json`, engine exit1. The fixture
starts a second passenger's real public boarding request, advances0.1s, cancels,
then updates rescue and retries the public request.

Cancellation now returns immediately when no boarding owner exists and clears
the rescue interaction only when its target matches the cancelled passenger.
The same regression passes afterward:
`tmp/crew-boarding-cancel-after-20260925/index.json`, engine exit0. It also checks
no cancellation teleport, no extra rescue completion, retained swimmer state and
unchanged310kg seated crew mass. Editor builds11.29s (regression) and12.73s (fix).
This qualifies interaction/pose ownership cancellation only; descending safely
to the water, mid-climb checkpoint cases and supported rendered motion remain
open. The prototype and this fix remain review-only and uncommitted, with no
new normal-game, standalone or packaged validation claimed.

### Reference for staged contact design

[Andy Hinton, NRS: Guide School: Damage Control](https://community.nrs.com/duct-tape/2019/04/19/guide-school-damage-control/)
is dated April19,2019, with July10,2023 also displayed. Its self-reentry section
describes side-tube access, a hand on a line/ring and another on the tube,
upper-body support over the tube, then an inward handhold. This supports a staged
approach/contact/pull-over design rather than direct interpolation to a seat.
It supplies no measured motion trajectories, timings, joint angles or dimensions.
No source photos are downloaded, copied into assets or licensed for redistribution;
the page credits Southeastern Expeditions and Chugach Outdoor Center for photos.

A new event-only `FindBoardingTubeSupports` helper selects separated points on
the published section0 tube triangles, upper half with upward-supporting slope,
on the swimmer's side. Central-half preference and slope/spacing bounds are
authored selection heuristics, not measured anatomy or grip/friction guarantees.
Output is raft-local and fails closed with no valid pair. It does not install a
new trajectory; the rejected arc remains disabled in ordinary play. Runtime
integration must still preserve the selected surface under deformation, solve
reach/arm lengths, review body clearance and transfer support before release.

Editor rebuild succeeds in170.72s. D3D12 receipt
`tmp/crew-boarding-support-query-20260925/index.json` reports1success,
0warnings/0failures/0not-run, engine exit0. Selected fixture supports in raft-local
centimetres are(-129.388,84.354,20.351) and(-81.031,86.937,21.773), rounded by
the engine vector formatter. The test independently checks rendered-hull distance
<0.00001m, distinct supports, selection covariance within0.001cm after a rigid
translation/rotation, opposite-side selection, and rejection of zero spacing.
Existing cancellation/occupancy/PFD assertions still pass. The unchanged hand-gap
measurement confirms this helper alone has not repaired the rendered trajectory.
Next integrate a reach pose using these surface points and check anatomical reach
and body clearance before any pull-over or seat transfer.

### Integrated reach key pose (still review-only)

The latest prototype replaces the rejected60cm sine lift with two stages:
start-to-tube reach, then the still-unqualified seat-transfer placeholder.
The reach transform faces inward using the selected support-pair axis and
positions the current hand midpoint at the supports; individual hand controls
are mapped back into that transform. A3cm upward palm-center offset,35percent
reach boundary, minimum4s duration and80cm/s nominal path rate are authored
parameters, not measured rescue biomechanics. Body/PFD consume the same staged
published pose. Ordinary gameplay still does not enable this prototype.

Editor build177.12s succeeds. Actual D3D12 capture receipt
`tmp/crew-boarding-reach-20260925/index.json` reports1success/0warnings/0failures,
engine exit0. The transition takes343updates, maximum root step2.101126469cm.
Reach boundary frame120 is saved in
`tmp/crew-boarding-reach-views-20260925/frame_120.png`; additional inspected
frames180and240 show the subsequent transfer going through the tube/raft.
The former airborne lift is gone, but this is NOT a validated climb. Remaining
work is a supported torso-over-tube phase, leg clearance and inward handhold
transfer before seat placement, plus deformation, interruption and game checks.

The whole-transition minimum hand gap0.654306987cm is not acceptance evidence:
small unsigned distance can also occur while penetrating. The follow-up test
therefore checks both hand controls at the reach boundary specifically and
compares shoulder-hand spans with the starting pose (no increase over2cm).
Those control-span checks still do not establish anatomical joint limits,
rendered palm contact, body collision safety or support forces.

The stricter boundary test passes in
`tmp/crew-boarding-reach-boundary-20260925/index.json` (1success,0warnings,
0failures,0not-run; engine exit0). Maximum of the two hand gaps at the boundary
is2.539933526cm; both control-span assertions pass. Test-only rebuild12.16s.
The no-opt-in native occupancy regression also passes in
`tmp/crew-boarding-reach-default-20260925/index.json`, engine exit0. This is not
a new normal-menu motion/performance run or standalone/package validation.
The accumulated default-off prototype is being checkpointed in Git; local
captures and unrelated work are excluded. It must remain disabled until the
remaining supported transfer and collision/animation gates are satisfied.

### Intermediate hand-anchored posture

The next default-off candidate holds the reach root from35to60percent of the
transition and leaves both hand controls at the same targets. An authored torso
shift puts its center5cm inboard and20cm above the hand midpoint; head, shoulders
and hips receive the same shift. Legs fold outboard using normalized direction
interpolation, preserving the existing thigh/shin target spans rather than
shortening them with endpoint interpolation. These are authored posture rules,
not measured biomechanics, anatomical validation or a force-supported solve.

Editor rebuild85.96s succeeds. D3D12 receipt
`tmp/crew-boarding-pull-20260925/index.json` reports1success/0warnings/0failures/
0not-run, engine exit0. Across86pull samples the maximum of both hand distances
is2.540161718cm and maximum leg-span change rounds to0.000000000cm. The full
prototype takes343updates; maximum sampled root step3.414265516cm.

Actual engine frames180and206 in `tmp/crew-boarding-pull-views-20260925` show
legs hanging outside during the intermediate posture, unlike the prior direct
seat transfer. These dark single-view captures do not establish skin clearance
or physical contact forces. Frame270still shows the subsequent transfer passing
through the raft. Do not promote this candidate: inward support transfer and a
leg-clearing traversal to the assigned seat are still missing. Captures remain
local; ordinary boarding and cooked river assets are unchanged.

No-opt-in native regression `tmp/crew-boarding-pull-default-20260925/index.json`
also passes1success/0warnings/0failures/0not-run, engine exit0. This remains an
editor-native regression, not normal-menu motion/cost or packaged acceptance.

### Rendered-boot transfer clearance: failing gate

The next native audit reads every LOD0 vertex from both visible production boot
components, transformed into raft-local coordinates after actual pose publication.
It samples every6updates during the post-pull transfer and queries the reference
uploaded tube/floor upper envelope at each vertex XY. Unavailable CPU vertex data
or empty samples fail the test rather than counting as clearance. This is a
conservative top-envelope deficit, NOT signed solid containment, continuous
collision detection, all-body clearance or a frame-performance measurement.

Run with both `-RaftSimTimedReentryReview` and
`-RaftSimRequireBoardingTransferClearance`. The strict option rejects sampled
deficit>2cm; this authored diagnostic tolerance is not river acceptance. Supplying
the strict flag alone fails closed rather than silently testing default boarding.

`tmp/crew-boarding-boot-clearance-20260925/index.json` reports0success/1failure/
0warnings/0not-run, engine exit1: exactly the transfer upper-envelope assertion.
Across350662supported vertex samples, the maximum deficit is42.393345562cm at
frame252, `ProductionLeftBoot`, raft-local point(-48.180,73.440,-16.059)cm.
This quantifies the previously observed hull-crossing transfer. Keep the gate
failing until a genuinely leg-clearing path passes it; do not relabel unsigned
hand proximity or occupancy success as collision acceptance.

The first test build failed on `auto*` deduction from Unreal's object pointer;
explicit `const UStaticMesh*` corrected it. Builds12.69s and12.62s then succeeded,
the latter adding a CPU-buffer availability guard. No runtime animation changed
in this audit. Next resolve leg-over-tube support before root travel to the seat;
the42cm deficit is too large to treat as a sole-offset adjustment.

### Leg-over candidate and dense completion-frame audit

The review-only controller now holds the root at the tube through lift/leg-over
before travelling to the seat. Two-bone knee controls preserve segment lengths;
segment reachability is checked before mutating boarding state. Targets are
authored (foot height25cm above hand targets), not measured human motion. A stable
sideways bend pole is blended while feet remain outside. Boot splay fades toward
the actual planted end orientation during settling. Ordinary boarding stays unchanged.

Retained failures: `tmp/crew-boarding-legover-20260925/index.json` failed boot
clearance at18.884cm. Correcting end boot orientation passed sparse sampling,
but strengthened per-update tests exposed a54.298cm right-knee jump atframe247
(`tmp/crew-boarding-legover-joint-20260925/index.json`). The stable bend-pole
repair addresses that discontinuity without weakening either limit.

Final native D3D12 run:
`tmp/crew-boarding-legover-complete-frame-20260925/index.json` reports1success,
0warnings/0failures/0not-run, engine exit0. Strict sampling now includes every
post-pull update and the completion frame:1,956,174 supported boot vertices;
maximum upper-envelope deficit1.633426454cm atframe306, unchanged2cm threshold.
Largest knee/foot control step6.120569828cm atframe291 (left knee), under10cm.
137 anchored samples have maximum both-hand gap2.540161718cm and zero reported
leg-span error. The completion-frame test build succeeded in12.72s.

No-opt-in follow-up `tmp/crew-boarding-legover-default-20260925/index.json` also
reports1success/0warnings/0failures/0not-run, engine exit0. This validates the
native occupancy regression only, not normal-menu or packaged performance.

Local engine captures remain in
`tmp/crew-boarding-legover-stable-views-20260925/`. Earlier candidate views show
close/occluded passage through other seated crew. These checks do not establish
whole-body or crew-to-crew clearance, continuous collision, moving/deforming
raft behavior, other identities/sides, interruption safety, partial support loads,
normal-menu motion/cost or packaged acceptance. No river/cooked assets changed;
do not enable the prototype or claim a delivered playable animation improvement.

### Expanded skinned-body audit rejects promotion

The next audit samples CPU-skinned LOD0 body vertices without the seated-glute
sampler's fixed spatial filter. It runs every6updates after the pull stage and
on completion, querying the same conservative raft upper envelope. Empty CPU
data, nonfinite points or missing production visual fail closed. Strict transfer
validation now also requires body deficit<=2cm; the boot gate is unchanged.
This includes skin covered by boots/equipment and does not prove signed solid
penetration or visible intersection. No additional per-frame production work.

Editor builds51.05s and14.30s succeeded. Native D3D12 results:
`tmp/crew-boarding-body-envelope-20260925/index.json` and the attributed follow-up
`tmp/crew-boarding-body-attribution-20260925/index.json` fail exactly the new body
envelope assertion (0success/1failure, engine exit255; Unreal reports-1).
Across585036 supported body samples, maximum deficit17.020253100cm occurs at
frame300, LOD0 vertex9511, raft-local(49.677,37.969,-1.367)cm,
avatar-local(36.758,24.891,7.902)cm. Boots retain1.633426454cm maximum deficit
over1956174 supported samples. The passing boot-only receipt above is not a
passing expanded-clearance receipt.

Actual retained engine frame240 was inspected: the dark, oblique view occludes
body contact and cannot establish clearance. Body foot bones intentionally use
0.35 rest scale beneath production boots, so identify vertex9511's skin influences
and inspect ankle/calf deformation before calling this visible penetration or
changing the motion. Do not hide the sample or relax the gate to obtain a pass.
Other crew, equipment, continuous collision and normal-play acceptance remain open.

After expanding the audit, the no-opt-in native regression
`tmp/crew-boarding-body-default-20260925/index.json` passes1success/0failures/
0not-run, engine exit0. No default-path promotion or packaged rebuild occurred.

### Right-calf attribution

`tmp/crew-boarding-body-influences-20260925/index.json` reproduces the same body
envelope failure, engine exit255 (Unreal-1). The vertex's actual LOD0 render-section
bone map and skin weights identify `calf_r=60138`, `foot_r=5397` (sum65535),
approximately91.8% calf and8.2% foot. This is not a purely collapsed foot vertex.
The audit now retains these influence names/weights for the worst body vertex.

Code inspection: SetSegmentBone preserves reference scale while rotating its
source shaft onto the desired control direction and placing its start. Calf
and foot heads are positioned separately. Thus a shorter knee-to-foot control
span does not itself shorten calf-dominant skin to that span. A source-length
calf/ankle mismatch is the next repair hypothesis, not yet a verified causal fix.
Measure the transformed source endpoint against the ankle control and review
skin continuity before modifying leg transforms across ordinary seated poses.
Do not inflate boot offsets or remove calf samples to pass the clearance test.

The attribution test initially failed compilation for shadowing the existing
Body configuration variable. Renaming the local to PosedBody fixed compilation;
Editor build14.05s succeeded. Absolute-path patch writes temporarily failed;
workspace-relative apply_patch succeeded with no ACL or data changes. No runtime
animation, source assets or acceptance limits changed in this attribution step.

### Calf shaft-fit experiment: endpoint repaired, clearance still failing

Default-off `-RaftSimFitCalfSpanReview` scales only the source calf's dominant
local shaft axis to the requested knee-to-ankle span, preserving transverse
scale. It requires axis alignment>0.9999; this source reports local(0,-1,0).
The first measured calf source span45.986578586cm exceeds the target34.365680555cm.
The transformed source endpoint error decreases from11.620898031cm to
0.000000245cm. This verifies the endpoint defect and candidate correction, not
all skin deformation or all identities/poses. The flag is cached once; ordinary
leg scale stays unchanged. Source assets and control spans are not modified.

Editor build47.01s succeeded. Actual D3D12 run with timed boarding, strict
clearance and calf fitting: `tmp/crew-boarding-calf-fit-20260925/index.json`
fails the body-envelope gate, engine exit255 (Unreal-1). The maximum is now
15.218177159cm atframe264, vertex8149,100% `ring_03_l` weighted; raft-local
(-109.830,72.101,10.943)cm, avatar-local(78.107,-12.638,25.036)cm. There are
584831 supported body samples. This does not prove all calf samples clear;
the worst vertex changed. Fingers below an upper envelope require actual
surface/solid contact review, not automatic relabeling as acceptable grip.

Captures: `tmp/crew-boarding-calf-fit-views-20260925/`. Actual frame300 inspected;
the oblique dark view still occludes lower-body contact. No visual acceptance.
Next quantify calf-region skin clearance and inspect hand/tube geometry with
adequate close views; verify ordinary seated/rowing/high-side skin continuity
before enabling longitudinal fitting. Keep strict gates unchanged and both
review options disabled in normal play. No normal-launch cost or packaged
acceptance claimed from this experiment.

Final cached-switch build11.59s succeeded. No-opt-in native regression
`tmp/crew-calf-fit-default-20260925/index.json` passes1success/0failures/0not-run,
engine exit0. Its measured fit=0 leaves the same11.620898031cm endpoint error
before/after, confirming the experimental fitting is not enabled in normal play.

### Palm target versus wrist pivot; remaining final handoff failure

Native `tmp/crew-boarding-finger-contact-20260925/index.json` reproduces the
15.218cm deficit. At its worst ring-finger point the exact rendered-surface
distance is2.824726254cm and raw section0 solid-angle winding is1.000000000.
These are consistent with an interior point, not merely a harmless finger below
the vertical top envelope. Winding is diagnostic only: closure/orientation and
continuous collision are not certified. It is measured at the failing frame,
not against a later pose. This test-only query does not run in normal gameplay.

Reentry previously placed the imported wrist pivot at the authored palm target
and retained reference orientation. The disabled prototype now publishes a
smooth palm-support blend. Its CC0 hand transform offsets the wrist using the
same source knuckle anchor convention as paddle grips and aligns fingers inward,
palms down, with mirrored handedness. The blend rises through reach, stays full
through leg-over, and fades during settling; ordinary poses keep blend0.

Builds36.65s (contact diagnostic) and119.33s (palm candidate) succeeded.
`tmp/crew-boarding-palm-support-20260925/index.json`, with calf fitting and strict
timed boarding, still fails exactly the body-envelope assertion, engine exit255.
Across583728 supported body samples the maximum is12.470056895cm atframe342,
vertex8153,100% `ring_03_l`; raft-local(148.105,-57.637,18.568)cm,
avatar-local(33.108,4.360,24.492)cm. Surface distance11.079095918cm, tube winding1.

The remaining worst point is now near completion, where the prototype fades
toward non-paddle reference hand orientation while its destination hand targets
come from a seated paddle pose. Next repair the full wrist/orientation/finger
handoff to that actual destination, with continuity and surface checks. Do not
claim the supported interval fully clear from only the changed global maximum.
No new visual acceptance, default promotion, packaged build or performance claim.

No-opt-in native regression `tmp/crew-palm-support-default-20260925/index.json`
passes1success/0failures/0not-run, engine exit0. Strict prototype failure remains
recorded and neither review option is enabled by default.

### Destination-grip handoff and explicit wrist/finger continuity

The review-only boarding pose now publishes a separate paddle-grip blend while
the paddle prop remains hidden. Wrist offsets keep full palm anchoring through
the support-to-grip transfer, rather than fading back to bare reference wrists.
The CC0 adapter blends toward the actual stored seated destination's hand basis
and parent-local finger shape. The existing destination contact solver is reused;
the moving wrists are restored before the finger blend is applied. Ordinary
poses retain zero boarding blends and the existing full paddle-grip path.

New native observation tracks all32 wrist/finger bones on every update, including
completion. It requires finite transforms, position steps below10cm and rotation
steps at most30degrees per1/60s update; these are continuity checks, not anatomical
or collision acceptance. The body/boot2cm clearance limits remain unchanged.

Retained experiments, all with timed boarding, strict clearance and calf fitting:

- `tmp/crew-boarding-grip-handoff-20260925/index.json`: the first intermediate-pose
  grip blend fails body clearance at8.825065092cm, frame270, vertex6151,
 100% `thumb_03_r`. Position step8.925388515cm but rotation step168.426164076degrees.
- `tmp/crew-boarding-grip-identity-20260925/index.json`: fixing shaft/T-grip identity
  alone is rejected and removed. Body deficit8.208083661cm, but position step
 15.012610516cm and rotation179.533444082degrees fail the expanded continuity gates.
- `tmp/crew-boarding-destination-grip-20260925/index.json`: solving the stored
  destination shape instead of continuously re-solving wrap direction against
  intermediate paddle points passes continuity:86handoff samples, maximum
 5.693478932cm step atframe291 (`pinky_01_l`), maximum6.607625101degrees atframe301
  (`index_03_r`). Strict test still fails only body-envelope clearance, exit1.

Final body result:583717 supported samples, maximum8.276833862cm atframe270,
vertex6151,100% `thumb_03_r`, raft-local(-68.422,76.005,17.728)cm. Exact surface
distance8.224789439cm and raw tube winding1 remain consistent with an interior
point. Boots retain1.633426454cm deficit over1956174 supported samples. Existing
137pull samples retain2.540161718cm maximum both-hand control gap and zero leg
span error. This does not establish that every other body region is clear.

Editor builds82.00s,79.20s and77.49s succeeded. Captures are retained in
`tmp/crew-boarding-grip-handoff-views-20260925/`,
`tmp/crew-boarding-grip-close-20260925/` (base color), and
`tmp/crew-boarding-destination-normal-views-20260925/` (world normals).
The wide frame330 and close frame270 were inspected: base color is too dark,
and the normal view makes geometry legible but other seated crew still occlude
the failing hand. None establishes normal shading, continuous motion or clearance.

Next resolve the right-thumb skin/support orientation and release path near
frame270 with an unobstructed exact-contact view; do not hide the vertex, raise
the tolerance or promote solely because the final handoff no longer flips.
Both experimental flags remain default-off. No standalone/package rebuild,
normal-play visual improvement, river geometry change or performance acceptance
is claimed from this candidate.

No-opt-in follow-up `tmp/crew-destination-grip-default-20260925/index.json`
passes1success/0warnings/0failures/0not-run, engine exit0. This verifies the
ordinary native occupancy regression, not rescue animation or packaged play.
