# Actual guide swim/reentry drill — unfinished

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
