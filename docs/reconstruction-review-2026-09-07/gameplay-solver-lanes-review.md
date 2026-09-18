# Gameplay solver-lane comparison: no default promotion

2026-09-18 UTC. The pending editor build completed successfully, all seven
selected native tests pass, and nine actual South Fork captures now establish
that eight lanes reduce solver time but do not consistently improve whole-frame
timing. Gameplay remains at four lanes. This is not visual or 30 FPS acceptance.

## Build and native verification

The same editor build session85099 completed all163 actions with exit0 after
1618.55 seconds; it was not restarted. Log:
`tmp/solver-lanes-editor-build-v1-20260918.log`, SHA256
`dae2687ebd56532f0155d1cd54f189a399bba04ece43e0654d16c2d5e7dc3580`.

The rebuilt editor ran with `-RaftSimSolverLanes=8`. Exported results contain
seven successes, zero warnings/failures/not-run/in-process tests:

- `RaftSim.Water.SolverLaneOption`
- `RaftSim.Clock.CommittedDetail`, `FixedQueue`, `NativeBridge`, `RaftFailureLatch`
- `RaftSim.M3.CartesianWindowExactOverlap`, `WaterDryRockSampling`

Report: `tmp/solver-lanes-native-v1-20260918/index.json`, SHA256
`9f2a64fb0b075e34df5cbcdecbcf217d2adb76f0a2b378d4bb7dbf9b4dfe4ab5`.
Runtime logs confirm eight diagnostic lanes and archive
`ae75e631be712a1dee7de53f2ca4b3508d406a1becf4346553806485c221b2a3`.
NullRHI native results do not establish rendering or whole-game performance.

## Actual game measurements

Every capture uses the same built editor, ordinary South Fork FullReach scenario,
station8330,1280x720,D3D12,RTX3060 Laptop GPU,RT0,900 CSV rows. The predeclared
inclusive sample range is60..840, target30FPS with p95 <=33.333333333333336ms.
No physics step, quality, geometry, contact tolerance or refresh setting changes.
No component comparison or stage-timing instrumentation is enabled.

All labels are `south-fork-lanes-<suffix>-v1-20260918`. CSVs, logs and process
reports remain under `unreal/Saved/Profiling/CSV`, `unreal/Saved/Logs` and
`unreal/Saved/RaftSimValidation`. Every wrapper and game exits0 without timeout.
Each verifies exactly one runtime lane limit and the linked archive hash, and
confirms the unchanged elapsed-frame mode before recording scope offset1.
The exact identified cook8900 is suspended and resumed successfully for every
capture. Complete arguments, CSV/log hashes and CPU observations are retained.

| Suffix | Lanes | FPS | Frame mean ms | Frame p95 ms | Solver mean ms | Solver p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| four-a |4|23.939995|41.771103|51.1936|8.351003|10.8595|
| eight-a |8|25.704446|38.903775|48.1330|5.497763|7.8581|
| eight-b |8|27.910583|35.828703|44.1648|4.812359|7.0414|
| four-b, source-search overlap |4|20.476798|48.835761|76.1725|11.289282|16.7014|
| four-c, clean repeat |4|26.189706|38.182941|45.6082|7.195814|9.7916|
| four-d |4|23.785845|42.041810|52.0899|8.421620|11.1826|
| eight-c |8|28.059017|35.639168|44.4033|4.637423|6.9010|
| eight-d |8|25.830479|38.713955|47.4232|5.276138|7.3628|
| four-e |4|26.503367|37.731055|45.4124|7.119350|9.7892|

**All nine fail the unchanged 30FPS p95 gate.** During four-b a source search
ran longer than expected; it was stopped, that result retained and explicitly
marked confounded before inspecting timings, and four-c was run without other
diagnostic work. Then a fresh uninterrupted four-d/eight-c/eight-d/four-e ABBA
sequence ran with other diagnostic work idle. It is not legitimate to silently
discard four-b or describe the first five captures as a clean four-run ABBA.

The clean confirmation's forward pair improves solver and frame timing, but its
reverse pair reduces solver mean7.119350 ->5.276138ms while frame mean worsens
37.731055 ->38.713955ms and p95 worsens45.4124 ->47.4232ms. Therefore the actual
whole-frame benefit is not reliable in both orders. The default is NOT changed.
These ordinary trajectories and shared-host runs are not identical physical
states; offline bit-exact worker qualification is separate evidence, not proof
of identical gameplay trajectories or sustained full-route performance.

Reports, with every requested row and all runs preserved:

- `tmp/south-fork-solver-lanes-comparison-v1-20260918.json`, SHA256
  `d0a840b30ba4538b5d162d96e9f14e45144662135ffbbdd43caaacccf5250ea1`.
- `tmp/south-fork-solver-lanes-confirmation-v1-20260918.json`, SHA256
  `1ff25807382490517cc3cdbc9c1b0dc38b3d5bd041e7e02c297e054f0964c322`.

Even eight-b's best p95 is44.1648ms. Its refresh-only cohort averages41.211471ms
and selection-only cohort31.380972ms with p9539.2662ms. Surface Tick averages
21.75ms; positive Refresh samples average20.11ms; CartesianPublish averages
10.22ms. These scopes overlap/nest and MUST NOT be added. Merely increasing
lanes or staggering refresh/selection does not finish the performance work.
Do not repeat rejected base-vertex/history/packing trials without a new reason.
Next optimization must address substantive surface refresh/publication work,
retain exact state/geometry/contact gates, and pass actual-game comparisons.
No new visible improvement, motion/reference review or full-physics pass is claimed.

## Hydraulic continuation

The existing7950/local5000 reports were re-read and the new complete8000/
local6000 snapshot independently passes BOTH state and artificial-bank audits.
Both contain5,382,400 cells with all86,720 artificial-bank face cells exactly dry.

| Simulated time | Maximum depth m | Maximum speed m/s | Outflow m3/s | Inflow m3/s |
|---|---:|---:|---:|---:|
|7950|3.8081643237551797|5.350672614471525|102.9369635544263|45.30695454719997|
|8000|3.80661211849455|5.350916511053762|103.94413466896678|45.30695454719997|

Maximum step mass residual remains1.4395798775268531e-8m3. Neither state is
settled; installed4950 water remains untouched. Reports are
`tmp/control-ablation-{7950,8000}s-{state,banks}-v1-20260918.json`.
Depth hashes are respectively
`a9c35435689d3c93db04ee3b7d658510464d31f7ad99ba5166d8fe1f6c67fed0` and
`49834da1f8ffd97d1b6f7122cef3cc4c7652a27d2409b2d4c3e9ef4e231f22d2`.

Cook8900/startUTC2026-09-18T06:34:59.2598919Z/session68256 is verified live after
the final capture. Preserve this same job; next8050/local7000 requires its
completion marker and BOTH audits. Nonlinear runtime stays OFF. The complete
ordered terrain/water/scenario/crew/regression/normalization/release scope stays open.
