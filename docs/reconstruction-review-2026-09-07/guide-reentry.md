# Actual guide swim/reentry drill — unfinished

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
