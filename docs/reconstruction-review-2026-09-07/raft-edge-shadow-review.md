# Raft-edge patches: geometry and shadow discrimination

September23,2026. Follow-through on the inspected rapid motion, not a new visual
delivery. The dark irregular patches beside the raft are shadow-sensitive over
present water geometry. Do not fill them with extra water sheets, change captured
ground, delete positive water or widen the raft transmission aperture to hide them.

## Actual source and terrain evidence

A fresh installed FullReach capture exports the current carrier and player-view
matrix at screenshot23, game frame213/world11.6463491795s. This is the explicit
8330 rapid review start, not normal-start or reconstructed hull-clearance acceptance.
Four independent camera rays intersect the submitted CPU carrier; all source
corners are wet. Native terrain-only collision lies behind water on each ray:

| Pixel | Water slope | Minimum source-corner depth | Terrain ray distance behind water |
| --- | ---: | ---: | ---: |
|135,695|1.161761°|1.574486 m|3.093146 m|
|330,620|1.297067°|1.518618 m|3.298247 m|
|90,645|0.790080°|1.399056 m|3.140362 m|
|1000,640|2.038375°|1.782682 m|4.695204 m|

The first two lie at/near the visible left-side patches; the other probes retain
surrounding water controls. These are CPU counterparts, not a GPU visibility fence.
They exclude missing submitted geometry and terrain-in-front at these particular
rays, not every possible material/refraction/latency or other-occluder problem.
The original independent audit and its six input hashes are preserved in the
[durable receipt](raft-edge-shadow-review.json). All22 existing camera-ray and
submitted-shape regressions pass in0.71s.

Using the recorded raft focus and same-frame yaw, the four source-space probes
are approximately193,174,258 and124cm across the raft axis. All lie outside the
82×215cm fourth-power interior transmission aperture (quartic sums30.69,20.30,
97.63,5.43, all greater than1). This uses rounded logged yaw, not a new precise
GPU-mask measurement. The wider190×320cm foam exclusion is separate from that
floor aperture and must not be conflated with missing base water.

## Shadow control and retained failed attempt

The first shadow control requested `-DPCVars=ShowFlag.DynamicShadows=0`. Unreal
logged an ECVF_Cheat rejection despite process exit0. That attempted control is
invalid, and its receipt/log/images remain retained without being relabeled.

The capture helper now offers explicit `StartupDisableDynamicShadows`, restricted
to startup-render diagnostics and rejected for ordinary FPS capture. It sets the
development console before scheduling screenshots and requires an actual zero
response, rejecting missing/conflicting values and the engine rejection above.
Defaults remain unchanged. New PowerShell checks exercise the real parsed
production functions/command builder and pre-process guards; the existing identity
and no-cook suites also pass. No native code, module or shader was rebuilt.

Corrected control v2 exits0 and confirms `ShowFlag.DynamicShadows = "0"`.
Its inspected final image has no corresponding irregular left-side patches;
cast shadows on the raft/scene also disappear, as expected. Both captures retain
24 images. They are separate continuous trajectories: baseline station8350.414,
control8350.340m, with different frame IDs/raft yaw. This is qualitative causal
discrimination, not an identical-state pixel difference or a rendering fix.
The normal image and all process/log hashes are bound in the receipt.

All three capture processes are terminal; their cook suspend/resume statuses
are0 and the same original cook36692 resumes and advances. No scene/package,
source classification, ground/collision, installed4950 fields or nonlinear state
changes. Normal shadows stay enabled. The latest independent ordinary rapid
p9535.4787ms still fails33.333333ms; no timing is inferred from these screenshots.

## Next bounded implementation

Investigate supported filtering of Single Layer Water's existing virtual shadows,
not shadow removal or source/hull edits. Installed UE5.8 source declares both
`r.Water.SingleLayer.ShadersSupportVSMFiltering` (compile-time/read-only) and
`r.Water.SingleLayer.VSMFiltering` (runtime), both default0; the project enables
VSM but does not currently enable these water flags. This identifies a candidate,
not proof that it resolves these pixels or meets cost. Qualify shader support,
actual shadow-preserving motion and separate ordinary timing before any normal
configuration promotion. Do not repeat the invalid device-profile showflag attempt.
Breaking/froth, source interpretation, collision, shoreline, whole-route and all
later-river/crew/release gates remain open.
