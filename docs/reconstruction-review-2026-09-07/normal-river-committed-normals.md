# Playable current normals: displayed-frame clock connection

September14,2026. Saved installation and fresh independent graph audit PASS;
GPU regression PASS; actual gameplay capture inspected, visual acceptance FAIL.
First installer67237
terminated exit1 before any write: its overly strict MP_NORMAL-root assertion
rejected the saved registered-detail composition wrapper. The optical normal is
the wrapper's Base input, not the root. Corrected the guard to require reachability
and unchanged root; every-node checks still protect the wrapper's other branch.
Retry26849 TERMINAL exit0 with fresh v2 log:248.08s commandlet,0errors/5warnings.
Fresh read-only17553 TERMINAL exit0:0.40s commandlet,0errors/5warnings. All six
saved output graphs match exactly. Do not claim visual improvement or a30FPS pass.

The ordinary South Fork material is
`/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4`.
Its previous SHA was `e0c9613bc16125c0f991dc29c6421359cd0fbd6903ab0481657ed544bca55f2c`.
New saved SHA: `adb56123f1e07c7cdfe2f6cd0da2db1c2e44f12d8ebb147a640ad9899a73c0c3`.
All459 protected scene/profile files unchanged; zero new material expressions.
Backup SHA `0ba083cd49509d71dc5a057a2e7efb0d89087561a44cf3d27a03c0d78796c178`.
Foam lace and optical coverage already use `SouthForkCommittedFrothTimeV1`,
the phase associated with the displayed density frame. However,
`SouthForkCurrentGradientNormalV1.TimeSeconds` previously used MaterialExpressionTime.
The local-normal shader's stated common-clock contract was therefore not met:
normal highlights can keep moving on wall time while the displayed water holds.

The scoped correction connects that existing normal input to the SAME existing
committed clock node. No shader arithmetic, optical gain, spectrum, foam mass,
geometry, force, time step or additional expression is changed. The editor builder
receives the same connection after constructing the registered foam clock;
legacy parents without that clock retain their time source.

Build59707 TERMINAL exit0,53.83s. Absolute-path apply_patch writes failed even
with approved access; a no-write file-open diagnostic succeeded. The relative
workspace-path apply_patch then succeeded. No ACL, security setting or file
ownership was changed. Installer script:
`unreal/Scripts/integrate_south_fork_committed_normals.py`.
It requires exact old material hash, preserves a verified backup ZIP, changes
one input only, checks every other node and five protected output graphs, and
guards map/actors/captured ground/save hashes. A fresh read-only invocation is
required after saving.

## Capture limitations retained

Before any asset change, baseline92985 completed exit0 with old material.
`south-fork-normal-clock-before-v1-20260914` produced three1280x720 screenshots
and recording `unreal/Saved/VideoCaptures/RaftSim_20260914-030446.mp4`.
The default player camera is visibly obstructed by foreground character geometry.
Do not treat it as a clear comparative water view. Full decoding succeeds:
50 actual source frames over6.410s,192 encoded frames, maximum encoded PTS gap
0.0333333s. Encoded30Hz does not establish game30FPS; encoder repeats frames.
Existing ROI labels in the decoder are not calibrated for this obstructed view.

Explicit-camera retry99743 also ended exit0 but FAILED capture: river focus
8330,0 is dry/invalid and the runtime correctly refused its fallback. No new
recording/screenshots from that attempt. Do not confuse global launch review
station with a guaranteed wet fixed-camera coordinate. No actor teleport was
requested. Both ordinary-game launches log existing EditorToolset/ToolsetRegistry
Python initialization errors about missing AgentSkill/PythonTestRunner; these
are not a clean startup/release pass.

All captures share load with original replays/cook; none suspends them or changes
GPU power settings. They are not isolated performance comparisons. The last
valid ordinary benchmark remains18.899245FPS/p9570.33ms, failing desktop30FPS.

## Parallel stability investigation

Observer97152 matches original steps through0.2s. Early fastest cell[101,21]
drains from11.82mm at0.191667s to9.09mm at0.2s and6.93mm at0.208333s as speed
grows7.90→8.24→8.58m/s. At the original0.2s rate, pressure acceleration is
[-24.3807,-34.4093]m/s2 versus total partial velocity rate[-22.3099,-37.9455].
Pressure supplies most of that velocity growth; transport is not a matching
external velocity spike. This local decomposition does NOT prove a discretization
fix, energy instability or eventual full-history failure. Both mass and momentum
are falling as the cell drains. Main59896 subsequently exceeds120m/s but has
also shown a declining maximum; do not falsely describe monotonic divergence.

GPU regression48115 TERMINAL exit0: RegisteredFoamClockGPU passes all56 actual
queries; max circular phase error2.74553895e-6 below unchanged2e-5 gate. Held and
completed frames, moved registration, boundary wrap, disabled/legacy/GPU clocks
and100-million-second phase covered. This tests the shared helper, not visual
acceptance. Report `unreal/Saved/RaftSimValidation/committed-normal-clock-gpu-v1-20260914`.

Actual shore-camera12489 TERMINAL exit0, label
`south-fork-normal-clock-after-v1-20260914`. Three1280x720 screenshots captured;
001/002 visually inspected alongside the unmodified decoded1s frame. This is
the normal full-reach South Fork scenario with an ephemeral profile, only camera
and capture settings, no alternate water or actor teleport. It visibly contains
terrain, channel rocks and the current water material. Fine optical motion is
present, but foam still forms broad blurred patches and the slope/crest remains
too sheet-like for convincing breaking-water acceptance. No matched before/after
improvement claim: both earlier baselines were unsuitable. Material hash remains
adb56123...c0c3 after gameplay.

Recording `unreal/Saved/VideoCaptures/RaftSim_20260914-032925.mp4`:46 actual
source frames over6.372s; full decode191 frames through6.333333s, max PTS gap
0.033333s,8exact encoded duplicates after1s. Encoding repeats frames, not30FPS.
Existing decoder ROI labels are NOT calibrated to this new shore view; do not
compare ROI labels/statistics to previous camera or interpret as optical quality.
Follow-up check: the capture's CSV is zero bytes, not a usable shortened timing
record. The game exited at151frames before the300frame profiler finalized.
Normal-game startup retains pre-existing missing AgentSkill/PythonTestRunner
errors, so exit0 is not a clean release pass. No original replay/cook suspended.

Next: continue evidence-based wave/froth shape and full-history stability work,
with the clock correction retained in the normal playable parent.
Continue inspecting the observer's first speed doubling and conservatively
evolved cell quantities. Full geometry/wave/froth/stability/contact/30FPS, crew,
later rivers, release and final commit remain open.

Cook checkpoint8200/local4000 is COMPLETE; both independent state and bank audits
exit0. All5,382,400 cells finite;86,720 artificial-bank cells exactly dry.
Driver volume discrepancy6.9849193e-9m3, maximum step residual1.2619996e-8m3;
depth maximum3.799077m, speed maximum6.215394m/s. Outflow101.151589m3/s still
exceeds inflow45.306955m3/s: UNSETTLED, not normal-map integration. Depth SHA
`68485db8db91bd35ea331b51c3e9d9b4ef477eb6bc1486aefc32c00c1d7b21cf`.
Reports `tmp/south-fork-expanded-8200s-{state,banks}-v1-20260914.json`.
Original cook83142 continues untouched toward10000; next COMPLETE8300/local6000
needs BOTH audits.
