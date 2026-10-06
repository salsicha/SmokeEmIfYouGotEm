# Seated heading and fresh South Fork water review

September 18, 2026. The normal South Fork Full Guided Descent entry remains the
full river; Troublemaker remains a rapid, not a menu item. This work does not
qualify the unfinished breaking waves, froth, terrain or 30 FPS target.

## Fresh observations and cause

The ordinary startup recording `RaftSim_20260918-023531.mp4` contains 205 source
frames over 16.030 seconds. All 481 encoded frames decode through 16.0 seconds;
encoding at 30 Hz is not game FPS. Unmodified decoded 3/13-second frames and
startup PNG021 were inspected. Broad blurred foam patches, smooth wave faces
and tuft-like spray remain. No water shader, geometry or physics was changed.

The raft also leaves the default first-person view. A second actual capture,
`south-fork-camera-heading-baseline-v1-20260918`, distinguishes position from
orientation: the camera remains in the stern, while its yaw stays at 180 degrees.
Raft yaw changes from -160.840224 degrees at screenshot000 to -10.859809 degrees at023.
The corresponding camera/raft heading offset changes from approximately
-19.159776 to -169.140191 degrees. The player ends up looking backward off the stern,
not looking at the crew. The drift log's older `raft_dir_deg` is VELOCITY heading,
not hull orientation; it cannot establish the relative camera angle.

Both capture processes exited zero, saved all 24 required PNGs and finalized
recordings, and resumed the explicitly verified cook with return status zero.
Baseline instrumented movie: `RaftSim_20260918-024756.mp4`, 224 source frames,
15.968 seconds, SHA256
`10e3aa01cb4daaf68bd2faf71d427a65c21663b3f9043d5601d0a06aa5515ced`.
The first movie SHA256 is
`a5c4f1aec6925b52e2de3327091fefa32aa013b8e9c9a34337928e160ec318d2`.
Full decoding is not a claim to have watched every frame continuously.

## Runtime correction

The seated flat-screen guide carries the completed raft's yaw delta into the
controller's existing look direction. Mouse-look offset is retained; raft roll
and pitch are not added. The guide tick follows the raft/crew pose. Swimming,
chase cameras, other view targets, explicit non-controller review cameras and
stereo/HMD views do not receive this correction. Returning to the seated view
starts a new heading observation, never replaying turns made while away.
`-RaftSimWorldLockedGuideYaw` retains the old heading as a nonshipping control.
Source fields, water/contact geometry, timestep and nonlinear-runtime setting
are untouched. A native helper regression covers wraparound, 400 combined
turn/input steps, repeated observations, disable/re-entry and invalid poses.
The existing held-paddle mouse test now subtracts raft heading, so boat rotation
alone cannot falsely establish mouse input.

The capture log now records actual hull yaw and camera position in hull-local
coordinates alongside the existing rendered-camera observations. The rebuild
also exposed a real include-order dependency: the moving-water header used
`TStrongObjectPtr<UTextureRenderTarget2D>` with only a forward declaration.
It now includes the complete type, as required by the generated constructor.
Failed build `tmp/camera-raft-evidence-editor-v1-20260918.log` is retained;
the corrected v2 build succeeded. Final camera editor build succeeded in
17.85 seconds after the earlier complete camera build succeeded in92.55 seconds.

Native `tmp/seated-heading-native-v1-20260918/index.json`: all three tests
finished Success (two clean, one with warning), no failed/not-run/in-process.
Tests: `RaftSim.Guide.SeatedHeading`, `RaftSim.M6.RuntimeShell`, and
`RaftSim.WaterDetail.CompletedFrameContactGPU`. The shell warning concerns
render-thread access to `r.MotionVectorSimulation`; it is not waived or hidden.
Report SHA256:
`622efd27f9cb44a27a8561f60793f19ada5c17bc84dad36e1bd0391a57c70986`.
Standalone Development game build succeeded in178.59 seconds; executable SHA256
`b6a5850968d83c5a7eb596ce93f7e78c6ba4e70859ae39b4f5fcf2c7678fe8d9`.
This is not a packaged release build.

## Corrected playable capture and cost

`south-fork-seated-heading-normal-v1-20260918` exits0 without timeout and saves
all24 PNGs. In screenshots000/023, view-to-hull offsets are-19.159776/-19.267560
degrees; across all24 observations the range is[-20.018438,-19.070206] degrees.
These are camera-manager/actor observations, not an assertion of same-instant
pixel-perfect pose alignment. The raft turns while the crew remains in view.
PNG021 and unmodified decoded3s/13s frames were inspected: this is visible
normal-play camera progress. Rock shape, crew finish and broad soft foam remain
unaccepted; changing view direction does not improve their underlying assets.

Corrected recording `unreal/Saved/VideoCaptures/RaftSim_20260918-025649.mp4`:
206 source frames over15.927s, SHA256
`12efb11cbb335e8b6b3092031112bcaf15d5d79ecac07704b3a98b0b626f296e`.
All478 encoded frames decode through15.9s;18 adjacent decoded duplicates after
the first second. Both instrumented movies were fully decoded under
`tmp/seated-heading-decode-v1-20260918`. The two trajectories/times differ, so no
pixel-difference attribution or motion-calibrated water comparison is claimed.

Separate audit-free900-frame normal gameplay capture, fixed inclusive60..840
window:781 samples, mean42.5957425096ms (**23.476525FPS**), p95**52.3478ms**:
**FAIL30**, not a performance improvement. The corrected camera renders a
different view; do not attribute a timing difference to yaw arithmetic alone.
Runtime four-lane/archive and default CSV timing mode are confirmed. No build,
native test or decode overlapped this timing capture. Cook suspend/resume return
zero; its observed CPU delta across the suspension boundary is0.015625s, not
claimed to be exactly zero. Process exits0/no timeout. Frame audit
`tmp/seated-heading-frame-audit-v1-20260918.json` SHA256
`34b56daabac1a8eec40de863e59a8fe437cfc3468a92dae9e97d8c95713e3326`.
CSV SHA256 `e262a491f3cd0a5e1e496b3ddc79add804995a8eb4072317008b7084c9d8aaed`.
No sustained, all-scene, hardware-matrix or release acceptance is claimed.

## Hydraulic continuation

Complete8350/local13000 and8400/local14000 snapshots pass BOTH full-state and
artificial-bank audits. Each contains5,382,400 cells; all86,720 artificial-bank
face cells remain exactly dry. Maximum step residual is1.4754001131933592e-8m3.
At8400s, depth maximum3.791914672286744m, speed maximum5.352189480936071m/s;
outflow98.8481444199 versus inflow45.3069545472m3/s: still NOT settled.
Installed4950 remains unchanged. Reports are
`tmp/control-ablation-{8350,8400}s-{state,banks}-v1-20260918.json`.
Depth hashes, in order:
`3b5d6b0729be4792034bb878156593ec2cb839ada8802612706c457fc5037e2f`,
`9d28b0c6452e12c70437d54144d2126ee92fe12afd6ada08aafd14454aacbd87`.
The subsequent8450/local15000 snapshot also passes BOTH audits, with all86,720
bank cells exactly dry. Maximum depth3.79006267709358m, speed5.35228943976038m/s;
outflow104.0542319483 versus inflow45.3069545472m3/s: NOT settled. Its depth hash is
`2f4b9a4546c54e4a08504bba00702ee8342a9ee3307d722a98b9829478d3d392`;
reports use the same naming scheme with8450s. Cook8900/startUTC
2026-09-18T06:34:59.2598919Z was directly verified live after the captures.
Next8500/local16000 requires its completion marker and both audits.

## Remaining work

This camera fix is not a substitute for breaking-water delivery. The static
crest/toe envelopes and limited moving detail still do not reproduce convincing
breaking/froth. The exact storage/face representation regression was inspected
but NOT changed or resolved; neither were the block-preconditioner failures.
Nonlinear runtime remains OFF. South Fork reconstruction and physical coupling,
then Colorado, Pacuare, Futaleufu, Chilko/Zambezi reviews, crew quality,
normalization, outstanding regressions and release acceptance remain OPEN.
