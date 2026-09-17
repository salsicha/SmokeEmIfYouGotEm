# Startup water ordering — 2026-09-16

Follow-up: [installed first-frame water correction and remaining gates](startup-water-readiness.md).
The observations below describe the earlier ordering-only builds.

## Verified correction, not visual acceptance

The 24-frame, actual 1280x720 startup replay reproduces an absent-water first
image followed by visible water. No warmup frames were discarded. These runs
use the explicit paired 350-second terrain/water preview and full-hull review;
they are not default-map, settled-water, or performance acceptance.

The normal baseline initializes surface and stateful detail at the authored
launch before the run manager restores station 8330. The first detail center
was `(-11250,2400)cm`, thousands of metres from the requested rapid.

The water actor now registers its run-coordinate-provider tick prerequisite
when **the consumer** begins play. It builds the initial surface on its first
ordered tick, not during unordered BeginPlay. The provider remains a read-only
interface; no reverse project-module dependency or new hydraulic step exists.
Checkpoint selection, transactional wet-destination validation, source geometry,
water clocks, resolution, and quality settings are unchanged.

Actual replay `south-fork-startup-water-consumer-v1-20260916` exits 0 with all
24 frames. At frame 1, the destination water handoff completes at 23:11:37.097
UTC, surface publication follows at .167, and detail initializes at .171 with
center `(-541800,-359800)cm`. This proves corrected initialization location and
ordering, **not** successful initial rendering: image 000 is still dry and
image 001 has water with visibly unacceptable angular crests/froth and crew.

The PSO-delay diagnostic (`south-fork-startup-pso-diagnostic-v1-20260916`) and
render-lag diagnostic (`south-fork-startup-render-lag-diagnostic-v1-20260916`)
both finish with 24 frames and still have a dry first image. Logs confirm their
temporary CVar overrides applied. Neither override is in production and neither
run supplies FPS evidence. Next: trace the first material/mesh submission and
actual screenshot readback; do not conceal the problem with a capture delay.

## Native/build evidence and rejected experiments

Isolated gameplay DLL:
`tmp/startup-water-consumer-v1-20260916/UnrealEditor-RaftSimRaft.dll`, SHA256
`5ded08c35db8eac203fdf4f8d6f159db03f2e6b93399505635eeb455becbfc34`.
Corrected isolated project/test DLL:
`tmp/startup-water-consumer-project-v2-20260916/UnrealEditor-SmokeEmIfYouGotEm.dll`,
SHA256 `80ea60a9252778f3e2276e2b9cc394f3d62095a7ba8b83e7f181fbbd716b0394`.
Installed binaries and map assets are unchanged.

The first project-only experiments compiled standalone objects that were not
members of the actual unity link. Their captures do **not** test the proposed
StartPlay/producer registration changes; those edits were removed. Likewise,
the first native run discovered only three old tests, so it is not a pass for
the new regression. Rebuilding the actual linked unity unit corrected this.

Native session 60963 exits 0. The v2 report discovers and passes all four:
StartupWaterAfterSessionRestore, ReconstructedSessionContracts,
RunProgressDistinctFromRapidHydraulics, and CoordinateFrameProgress.
The new test starts the run before spawning the water carrier and checks the
dependency, absence of a reverse cycle, and unchanged prephysics tick group.
Report `tmp/startup-water-consumer-native-v2-20260916/index.json`, SHA256
`0e1c8def93918904ee8f636b988d4242d25451fd7b5155cfb99aa1ca426ce37a`.
Targeted Python preview/retention/session checks: **80 PASS**. No older failing
assertion or acceptance threshold was changed.

Full candidate detail replay **29793 / PID25548** is terminal PASS, label
`south-fork-consumer-order-detail-replay-v1-20260916`: eight post-ready handoffs,
5,599 fresh frames and 373.200019 detail seconds. The original 100-frame,
60-detail-second, 120-world-second and 900-second timeout gates are unchanged.
Visual/performance acceptance and normal project deployment remain false.
The scoped runner resumed all three temporarily suspended processes.
Detail report SHA256:
`d60df5185476b5bfc837d5926ba17f397b6f50be5c13dba4c09373412c399062`.

## Opt-in startup render audit

`-RaftSimStartupRenderAudit` records proxy creation, view relevance, mesh/buffer
readiness and actual material shader availability during the first eight frame
numbers. It uses read-only `GetMaterialNoFallback`; it does not request fallback
compilation, change rendering settings, or delay screenshot capture.

The v5 isolated gameplay module compiled and linked successfully, SHA256
`91c9d862791615055ca3013b814feeb397110f5361e0fb50a3dbfc1e56945b2c`.
Replay `south-fork-startup-render-submission-v5-20260916` exits 0, retains all
24 actual 1280x720 frames, and resumes the hydraulic cook successfully.
Render frames 4 and 5 submit initialized buffers with 57,690 and 147,651 indices,
but their material shader maps contain no LocalVertexFactory BasePass shaders.
Frame 6 first reports both NoLightMapPolicy BasePass vertex and pixel shaders.
This narrows the missing initial water to shader readiness; the opt-in audit
does not fix it. Whole-map completeness remains false even after those shaders
appear, so it is not a substitute for checking the required pass permutations.
No installed module, map asset, normal-menu delivery or FPS acceptance changes.

## Hydraulic continuation

The same 841-tile, 5,382,400-cell continuation reaches 1150 and 1200 seconds.
Both state and all 86,720 artificial-bank-face checks pass at each checkpoint;
all artificial-bank depths remain exactly zero. Both remain **NOT settled**.

| Absolute time | Maximum depth | Maximum speed | Volume | Total outflow |
| --- | --- | --- | --- | --- |
| 1150 s | 4.587177 m | 6.915398 m/s | 3,021,881.973 m3 | 72.308659 m3/s |
| 1200 s | 4.576625 m | 6.914774 m/s | 3,020,471.189 m3 | 74.629022 m3/s |

Inflow remains 45.306955 m3/s. Maximum per-step conservation residual is
1.298091e-8 m3. The continuing storage loss prevents settling acceptance.
Reports under `tmp/`, with SHA256:

- `control-ablation-1150s-state-v1-20260916.json`:
  `c7a676d2dbf1ca81496d58860ce508e04c8675e02f73d11b2f67f40fdd76b83c`
- `control-ablation-1150s-banks-v1-20260916.json`:
  `85dc82f13d99a1a39d71f6c1587c194c2bf213f2e113b22147e41ff3d6e71366`
- `control-ablation-1200s-state-v1-20260916.json`:
  `3f6407f8141ac6458318da2a416fcc52de90c4b6c0de1afc5871a4111056d82c`
- `control-ablation-1200s-banks-v1-20260916.json`:
  `cece2c936f565b3d244ae557ef0fd3129bc75ef2ea3055b8d0d94b52467b2912`

Next hydraulic checkpoint: local13000 / absolute1250 seconds, both audits.
The SM5 suite is now terminal FAIL: 51 clean passes, one warned pass, 31 failures,
zero not-run. The strict outer validator exits 1 despite the editor exiting 0.
Failures include exact represented-float/subnormal arithmetic, nonlinear owner
time stepping and total-depth integration. Two reconstructed fixtures explicitly
require SM6/FP64 and are incompatible with this SM5 run; they are not waived or
counted as passes. Report `tmp/sm5-resource-bindings-native-sm5-v1-20260916/index.json`,
SHA256 `f7e87aa1b7ca3c9ca4d2e1f05bd861825e1d9dbfd22f16a7d759968ad2601d87`.

Normal 30 FPS, coupled nonlinear water, terrain/rapid/foam/crew realism,
source closure/default delivery, Colorado -> Pacuare -> Futaleufu, other-scene
water, normalization and release remain open. Troublemaker is only a South Fork
rapid and is not a separate scenario/menu item.
