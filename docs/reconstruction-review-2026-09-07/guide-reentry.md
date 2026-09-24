# Actual guide swim/reentry drill — unfinished

## Swimmer surface-datum review — September24, NOT promoted

Drift previously integrates velocity without sampling the resulting position's
surface height; horizontal pulling likewise preserves the previous Z. New
`-RaftSimSwimmerSurfaceReview` tests attachment to the existing runtime water
sample at ejection, after drift and after pulling. Wet finite samples replace
only root Z; dry/missing/invalid samples preserve it. Authored pose offsets,
rescue gates and physics fields are unchanged. This is not a swimmer buoyancy
or dry-ground locomotion model. The flag is OFF by default.

Initial candidate Editor build173.28s succeeds with two existing D6 damping
double-to-float warnings. Four native suites succeed (3clean,1with retained
r.MotionVectorSimulation render-thread warning): SwimmerSurfaceDatum,
SwimmingTorsoAlignment, OccupancyControlsLoadsAndIntegratedMass and
M5.RuntimeRescueLoop. Report `tmp/swimmer-surface-native-v1-20260924/index.json`.

Actual normal-start candidate replay `south-fork-swimmer-surface-v1-20260924`
exits0 without timeout. This capture predates the review gate: attachment was
active without the later Review flag. Seven audit records across frames30,
60,90,120 match swimmer root and wet sampled surface exactly (60.349609375m
down to60.333343506m). Six-second reentry rejects,10s accepts,11s is seated/
attached with no active guide swimmer. No rescue gate was weakened.

Video `unreal/Saved/VideoCaptures/RaftSim_20260923-235611.mp4`, SHA256
`f8773d62c78515cbb76a4d677a21a96588fcf2c3bad3e5beb26c98fa557348f3`:
467decoded frames,15.533333s,20exact adjacent duplicates. Stills/report:
`tmp/swimmer-surface-decoded-v1-20260924/`. Inspected3s/6s show the nearby
stern underside obstructing much of the swimming view;11s restores seating.
This is NOT accepted visual behavior. Do not hide it with an arbitrary Z offset.
The raft drift log at frame144 reports support_delta_cm=0 and rendered floor
freeboard16.1cm, so these images do NOT establish a solver/render datum error.
Next qualify actual hull/swimmer/camera contact and intended immersion together.

The candidate was gated off after visual inspection. Gated-default Editor
rebuild succeeds14.68s; the subsequent source change is comment-only.
Gated-default standalone Game rebuild also succeeds95.05s. This is compilation,
not a packaged-executable launch or performance measurement. Neither
sample equality nor native tests establish rendered water agreement, motion,
collision or measured cost. No new normal-play surface attachment is delivered.

## Cumulative swim-event HUD correction — September24

The normal status line now calls GetSwimCount "swim events", not "swimmers".
RunManager increments this historical counter for a fresh overboard batch;
reentry does not decrement it. Scoring, rescue gates and active swimmer state
are unchanged. This resolves the misleading historical1 after successful
reentry, not a stale-rescue-state defect.

Editor build succeeds79.27s; standalone Game build succeeds113.61s. Actual
normal-start replay `south-fork-swim-event-hud-v1-20260924` runs rebuilt Editor
in game mode, exits0 without timeout, no cook workload. Throw-line drill
reenters at10s;11s telemetry confirms swimming0/mobility0/attached1/completed1.
Inspected11s frame shows the seated view and corrected "1 swim events" label.
This is not proof of launching the packaged standalone executable.

Original video `unreal/Saved/VideoCaptures/RaftSim_20260923-234331.mp4`, SHA256
`cfb87c103e35789a4aaf3dfa0e683a3fbe5a153eb9a97733aaab5f2e77c9b95d`.
Full decode:468frames,15.566667s,22exact adjacent duplicates,1280x720;
report/stills `tmp/swim-event-hud-decoded-v1-20260924/`. Full decoding is not
all-frame visual inspection, and encoded30FPS is not measured game FPS.
Water realism, continuous swim/boarding animation, collision and performance
remain unaccepted. Retained-scratch and parallel-presence candidates remain
opt-in following inconsistent whole-frame comparisons.

## Hull-relative pulling and actual-surface reentry distance

Pulling now stops at the rendered hull's conservative support plane with the
current visible posed body outside by5cm, rather than0.9m from raft center.
The target preserves swimmer elevation and follows the moving raft through
ReadyForReentry. Any drift into the envelope is projected outward; this is a
kinematic rescue constraint, not a physical collision solver. Pose changes
are applied before bounds queries and position is published to the avatar in
the same update. No geometry is hidden and nonlinear/shared-hull modes stay off.

RequestSelectedReentry now measures shortest distance from swimmer origin to
actual published visible hull triangles in world coordinates. This event-only
query prevents empty bounding-box corners authorizing boarding. The library's
1.35m limit and readiness gate are unchanged; distance means distance to the
raft surface, not its center. Tests check an actual hull vertex's zero distance
and explicitly reject a ReadyForReentry swimmer100m away while retaining both
swimmers and rescue_bring_to_tube feedback. Missing geometry fails closed.
The automatic recovering/capsize rescue path remains a separate legacy path
to audit; this does not qualify every rescue/collision mode.

Editor build with regressions succeeds47.97s (initial dependent rebuild291.97s,
two retained C4305 damping warnings). Occupancy, SwimmingTorsoAlignment and
M5.RuntimeRescueLoop all pass:2clean,1with the retained r.MotionVectorSimulation
render-thread warning,0failures. Report `tmp/swim-pull-native-v1-20260924/index.json`.

Actual normal-start `south-fork-swim-pull-reentry-v1-20260924` exits0 without
timeout; original cook36692 suspension/resume succeed. Throw-line succeeds
at3.493323m;6s reentry is rejected;10s succeeds;11s confirms seated attachment
and0current swimmers. Video `unreal/Saved/VideoCaptures/RaftSim_20260923-224459.mp4`,
SHA256 `f03c3eb60d9a1822c4b4d2fc0b3ca30690b2d235d5e7d9726c6aa01543c40c0d`,
fully decodes463frames through15.4s with13adjacent duplicates. Inspected
3s/6s/9s/11s frames keep the view outside the stern tube during pulling and
restore seating; prior6s tube-interior view is absent. Decoder artifacts:
`tmp/swim-pull-reentry-decoded-v1-20260924/`.

This is a bounded visible rescue improvement, not whole-cycle/all-side collision,
wet surface-height, boarding-animation or performance acceptance. Full source
reconstruction, water realism and queued rivers remain unfinished.

Standalone Game rebuild succeeds185.55s. Fresh900-frame ordinary normal-start
timing (samples60–840, confirmed nonlegacy FrameTime, scope offset1) fails:
mean34.250937ms, p9542.3028ms, maximum48.1943ms against33.333333ms. Engine exits0,
no timeout, original cook guard/resume succeed. CSV SHA256
`bee77a7374b19a6c0a2221b9eea004d3d426290ab6204731206839345554af83`;
audit `tmp/swim-pull-normal-frame-v1-20260924.json`. This no-active-rescue run
does not isolate the cost of new pull queries or establish a causal regression;
it does establish that this sample cannot pass the normal-play budget. Active
pull/reentry-event cost and repeatability remain to be measured separately.

## Initial rendered-body/hull separation

Initial ejection now projects the current rendered hull bounds and visible,
posed swimmer component bounds onto the ejection direction, moving the whole
body outside with5cm explicit clearance. These are conservative world boxes,
not a reconstructed collision hull or a continuous collision solver. The
event-only query does not scan mesh vertices every frame. The fixed circle is
only the starting candidate; no rescue distance/readiness gate is changed.
Native occupancy checks every visible component against the tilted/rotated
raft's rendered bounds, including feet. Occupancy and swimming pose suites
pass2success/0warnings/0failures in `tmp/swim-clearance-native-v1-20260924/index.json`.
Editor build with regression succeeds in16.94s; standalone Game build succeeds
in37.95s. No fresh frame-cost capture supersedes the existing measured failure.

Normal-start drill `south-fork-swim-clearance-reentry-v1-20260924` exits0 with
no timeout and successful original-cook suspension/resume. Throw-line succeeds
at3.737883m;6s reentry remains rejected;10s succeeds;11s is seated/attached with
0current swimmers. Video `unreal/Saved/VideoCaptures/RaftSim_20260923-223206.mp4`,
SHA256 `be61ef51653470234e58f3332f33d40bfdbda7cd446cf915d8c991000471624e`,
fully decodes464frames through15.433333s,15adjacent duplicates. Inspected
3s/6s/11s originals:3s now shows an exterior water-level stern view rather than
tube intersection;6s pulling still intersects the raft;11s restores seating.
Artifacts: `tmp/swim-clearance-reentry-decoded-v1-20260924/`.

This is a visible initial-ejection improvement only. Drift collision, wet
surface height, exact per-side/whole-cycle clearance and rescue pulling remain
unfinished. Next replace the fixed0.9m center-relative pull target with a
rendered-hull-relative target and audit all associated distance semantics;
do not enlarge1.35m reseat limits simply to pass. No performance acceptance.

## Preserve swimmer world heading on ejection

Ejection formerly replaced every avatar's rotation with identity while the
guide pawn/camera retained its world heading. In the normal-start drill these
directions differed by approximately180deg, placing the camera looking back
through the swimmer. SpawnSwimmers now retains the avatar's world yaw and
releases seated pitch/roll before applying the horizontal swimming pose. This
does not change rescue gates, hide geometry or enable shared-hull diagnostics.
The occupancy regression now ejects an avatar from a tilted,−137deg raft and
checks preserved yaw and released tilt. Occupancy, SwimmingTorsoAlignment and
SeatedHeading pass:3success,0warnings,0failures in
`tmp/swim-heading-native-v1-20260924/index.json`. Editor build73.55s and
standalone Game build94.69s succeed. No new frame-cost claim; the outstanding
measured frame-budget failure remains open.

Normal-start `south-fork-swim-heading-reentry-v1-20260924` exits0 without
timeout; original cook36692 suspension/resume both succeed. Throw-line succeeds
at2.545447m,6s reentry is rejected,10s succeeds,11s confirms seated attachment
and0current swimmers. Video `unreal/Saved/VideoCaptures/RaftSim_20260923-222446.mp4`,
SHA256 `a5a28e16b565aee76b9d00d6efc80802d6f527152c9586ceaec83bcea01e34d2`,
fully decodes465frames through15.466667s with11adjacent duplicates. Inspected
3s/6s/9s/11s originals no longer show the guide's vest filling the view, but
the camera still lies at/inside raft tubes during swimming/pulling. Reentry
restores the seated view. Artifacts: `tmp/swim-heading-reentry-decoded-v1-20260924/`.
This is partial visible correction, NOT swimming/collision/performance acceptance.
Next fix hull-relative ejection and pull-target clearance, not another camera mask.

HUD follow-through: RunHudWidget prints RunManager.GetSwimCount(), whose value
increments once per new batch of swimmers and does not decrease on rescue.
The11s value1 is therefore cumulative swim incidents, not stale current rescue
state. Its label "swimmers" is misleading and remains to be corrected; no
rescue-state reset is justified by that display.

## Swimming torso-axis correction — obstruction still open

The swimming pose formerly used88deg yaw, leaving the torso and worn PFD's
local long axis vertical despite horizontal authored hip/shoulder landmarks.
Normal pose evaluation now uses−88deg pitch: local+Z points toward swimming
shoulders along+X. No mesh is hidden, no rescue gate is changed, and ejection
placement is not yet corrected. A native regression checks hip/shoulder-axis
alignment, horizontal orientation, head direction and periodicity over101
phases on both sides. SwimmingTorsoAlignment, RigidPaddleAcrossActions and
OccupancyControlsLoadsAndIntegratedMass all pass with0warnings/0failures in
`tmp/swim-torso-native-v1-20260924/index.json`. Editor build succeeds in52.53s;
standalone Game build succeeds in67.18s. No new timing capture was performed;
the outstanding measured frame-budget failure is not superseded by these builds.

Actual normal-start drill `south-fork-swim-torso-reentry-v1-20260924` exits0,
without timeout; original cook guard, suspension and resume succeed. Throw-line
request succeeds at2.510660m;6s reentry is rejected;10s succeeds and11s confirms
seated attachment and no guide swimmer. Video:
`unreal/Saved/VideoCaptures/RaftSim_20260923-221800.mp4`, SHA256
`ee999c58128754af371010931cfa03f4cdb2916dcc9eec876134c577cb38285a`.
Full decode yields465frames through15.466667s,13adjacent duplicates. Inspected
3s/6s/11s originals show changed clothing orientation but continued near-field
raft/clothing obstruction during swimming;11s restores the seated view. HUD
still shows1swimmer at11s despite native state0, another unresolved discrepancy.
Decoder artifacts: `tmp/swim-torso-reentry-decoded-v1-20260924/`.

This corrects a normal animation transform, not whole-body fit, swimming
visibility, hull clearance, motion continuity or performance acceptance. Next
resolve actual rendered-hull ejection/pull-target clearance and avatar/camera
orientation ownership. Shared indexed hull collision remains diagnostic-only;
do not enable it or hide geometry to mask this failure.

## Posed swimming eye and successful state transition — visual failure retained

The normal guide tick now resolves swimmer detachment/reboarding before eye
placement, follows the actual posed guide head in swimming as well as seating,
and keeps its own head hidden while its first-person camera is active. Chase
and external views retain their visibility gates. Editor/Game builds succeed
in51.07s/185.21s. This corrects stale seated-local camera placement but is NOT
a complete swim-view fix.

The drill has an explicit `-RaftSimGuideReentryThrowLine` option. Fresh normal
scene/start run `south-fork-swimming-eye-reentry-v1-20260924` uses the existing
throw-line range/aim/readiness gates: request succeeds at2.741082m, progresses
LineInFlight→Pulling, rejects premature6s reentry, then accepts10s reentry.
At11s the guide is no longer a swimmer, mobility is InRaft, attached to the
raft, completed rescue count1. The timer's immediate10s sample precedes the
next pawn tick; it correctly still shows detached mobility. Control yaw is
stable−179.993865deg while swimming, then−179.954884 at11s versus raft−178.876988.
The retained≈1.08deg look offset is not reset to the spawn heading. No manual
swimmer deletion, readiness bypass or teleport was used. Engine exit0, no
timeout, exact original-cook guard/resume succeeded.

Video `unreal/Saved/VideoCaptures/RaftSim_20260923-220229.mp4`, SHA256
`94338e4fc84fe3bf5932b14b6e19fb9505bce5155887110cc739553ade9839fb`, fully decodes
465frames through15.466667s with15 adjacent duplicates. Original3s/6s/9s/11s
frames inspected: swimming views remain obstructed by close-up vest/raft
geometry;11s restores the seated view. State-transition success does NOT accept
swimming visuals, animation, collision, all-frame continuity or performance.
Artifacts: `tmp/swimming-eye-reentry-decoded-v1-20260924/`.

Source inspection identifies the next concrete geometry issue: SpawnSwimmers
uses a world-axis1.5m circle regardless of hull dimensions; default footprint
length4.3m has half-length2.15m. Bow/stern ejection can lie within the footprint.
Verify actual hull-relative clearances and correct ejection positions using the
shared hull geometry. Do not mask the problem by hiding the raft/other crew or
loosening rescue gates. No body-hiding workaround was added. Native occupancy,
seated-heading and CameraWeather suites pass (2clean success,1success with the
retained r.MotionVectorSimulation render-thread warning,0failures), report
`tmp/swimming-eye-native-v1-20260924/index.json`. The full queued reconstruction
remains unfinished.

The previous overboard capture excluded the guide. A new explicit
`-RaftSimGuideReentryReview` capture-only option exercises the guide swimmer
through the existing SpawnSwimmers/occupancy path. It schedules guide ejection
at1s, an aimed ReachGrab at3s, and ordinary RequestSelectedReentry calls at6s
and10s. No swimmer removal, forced completion, teleport aboard, extended rescue
range or altered readiness gate. Other scripted crew inputs are rejected when
combined with this option. Normal gameplay receives no drill input.

Editor build succeeds in290.66s, retaining the two existing C4305 warnings in
RaftSimD6ChaosMeasuredRunner.cpp. The actual normal-map, normal-start run
`south-fork-guide-reentry-motion-v1-20260924` exits0 without timeout and resumes
the original cook36692. At2s the guide is swimming and the pawn detached.
The3s reach request returns false, rescue phase Failed; both reentry requests
return false. No rescue completes and the guide remains swimming at11s.
The control yaw stays−179.974848deg while raft yaw changes−179.609166→−178.878383.
This verifies a bounded swim gate, NOT reentry or all camera behavior.

Recording `unreal/Saved/VideoCaptures/RaftSim_20260923-215603.mp4`, SHA256
`85d0716e1fe60ecd2a3b93881a0006b5eef6e39186731382814a1f7eccc5db51`, fully
decodes464frames through15.433333s with8 adjacent duplicates. Original3s/11s
frames were inspected. The3s HUD explicitly reports rescue_out_of_range and
3.0m; the later HUD reports rescue_not_ready. **The swimming camera is beneath
or intersecting raft/crew geometry**, a visible failure requiring investigation.
Decoder artifacts: `tmp/guide-reentry-motion-decoded-v1-20260924/`.

Next inspect the swimming camera/anchor and swimmer-to-hull positions, and
exercise a valid existing rescue input (e.g. throw-line or swimming closer)
without weakening distance/readiness gates. Do not rerun unchanged ReachGrab
and expect reentry. Existing native OccupancyControlsLoadsAndIntegratedMass
and SeatedHeading regressions pass (2success/0failure/0warning), report
`tmp/guide-reentry-native-v1-20260924/index.json`; they do not qualify actual
reentry. This is diagnostic delivery only; standalone Game rebuild
and actual reentry remain outstanding. Installed
water fields, terrain/collision and nonlinear OFF are unchanged.
