# Actual guide swim/reentry drill — unfinished

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
