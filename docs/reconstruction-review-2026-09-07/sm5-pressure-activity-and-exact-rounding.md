# SM5 pressure activity and exact-rounding corrections

Recorded 2026-09-17 UTC. This advances production shader correctness; it is
not full-step, playable-scene, visual-water or 30 FPS acceptance.

## Pressure activity guard

The earlier hardware/WARP trace first diverged at acceleration phase 6.
An isolated dispatch using freshly uploaded captured inputs reproduces the
same failure, excluding the preceding dispatch sequence as a necessary cause.
Local instrumentation reads Control activity values `(1.0, 1.0)` on both
backends, but the float-zero guard broadcasts GroupInactive=1 on hardware
and 0 on WARP. Hardware then skips Scratch and Partial writes. A read-only
Control SRV variant and an equivalent combined early-return guard do not fix
the failure; neither is adopted.

Production now compares the activity flags' integer representations after
masking the sign bit, preserving positive/negative zero. These control values
are encoded boolean flags. The change does not remove inactive/invalid
guards, alter the operator, inject CPU pressure, change the 40-iteration
budget, relax residual tolerances, floor depth, or close wet connections.

The isolated corrected phase matches WARP exactly. All 18 original unscaled
transport-to-pressure fixtures now pass on hardware and WARP. For hardware
case 2, force relative error changes from 1384.53 to 8.20567e-8, and true
residual from 1070.72 to 6.06559e-8. Hardware case 17 true residual is
1.50917e-7, below the unchanged 2e-5 gate. Phase counts/order and diagnostics
are checked separately; these remain fixture passes, not RK2 acceptance.

Two new actual-GPU tests exercise 20 cases per backend: each active pole,
both poles, inactive and signed-zero flags, invalid-data rejection, 221-cell
padded and 561-cell multi-group dispatch. Exact sentinel comparisons prove
inactive/invalid outputs remain untouched. The original shader fails the
six active/valid cases on hardware; the corrected shader passes all 20.
Together with full fixtures and existing negative controls, **eight tests
pass**, no skips, using the production phase-6 bytecode.
That coupled run retains the previously qualified transport bytecode and
unchanged pressure phases, replacing only phase 6 with a fresh production
compile. Its shader SHA-256 is
`7a78374f008dbc9b0a8f2d738b5a36d2eb3a471d2b6ed6260781d07a64b0ca25`.

## Exact dyadic rounding

The original 29-test engine replay has ended (1 pass / 28 failures), releasing
its source freeze. The previously isolated exact hydrostatic correction is
now applied: integer result bits merge before a single float bitcast. The
dyadic arithmetic, stencil, rounding rule and rational oracle are unchanged.
The applied source matches the qualified local candidate after newline
normalization. Fresh compilation from production passes all **4,301 exact
face fixtures on hardware and WARP**, with zero arithmetic, transported-input
or operation-tag errors. Existing FXC warnings remain; this is not a
warning-clean release build.
The fresh production exact-face bytecode is identical to the earlier qualified
candidate: SHA-256
`07339b8bf095fbba3852a9957e615f20a250c06d2bc60ddbd145c6adb91061b2`.

A separate fresh six-phase production transport build is live in session
60207/PID 28144, start UTC `2026-09-17T04:05:32.7419036Z`.
Phases 0-2 are compiled; phase 3 is pending. The combined transport, coupled,
arithmetic and binding regression suite is queued behind this same process,
not yet a pass. Preserve its inputs and original handle. Witness:
`tmp/sm5-transport-production-v1-20260917-process.json`; queued report:
`tmp/sm5-production-correction-regression-v1-20260917.xml`.

Separately, the current harness with the previously qualified transport
bytecode and freshly compiled production exact-face shader passes all 46
transport, arithmetic-harness and resource-binding checks in 103.20 seconds.
With the eight coupled/guard checks above: **54 focused tests pass**, no skips.
Report: `tmp/sm5-pressure-guard-remaining-regression-v1-20260917.xml`.
This does not replace the queued fresh six-phase rebuild or native replay.

## Native integration replay

A fresh SM5 D3D12 engine replay is running, session 55459, PID 36412,
start UTC `2026-09-17T04:04:16.3178062Z`. It preserves the prior 29-test
selection and adds NonlinearAccelerationGPU, NonlinearPressureGPU,
TotalDepthTransportGPU and PressureResidualQualificationGPU (33 total).
The arithmetic fixture now covers exact faces, and the transport fixture
is the original unscaled 18-case set. Other fixture inputs are unchanged.
Acceleration/pressure native tests cover fused and unfused execution.
All 63 shader inputs and fixture hashes are recorded in the process witness;
preserve them until this exact process is terminal. No restart on timeout.
Installed DLLs are unchanged. Do not infer native success from standalone
passes or an engine exit code without the complete test report.

Local evidence (already ignored, not committed):

- `tmp/sm5-pressure-guard-production-tests-v1-20260917.xml`: eight passing tests.
- `tmp/sm5-pressure-guard-coupled-hardware-v1-20260917.log`: all 18 fixture metrics.
- `tmp/sm5-pressure-guard-baseline-v1-20260917.log` and
  `tmp/sm5-pressure-guard-hardware-v1-20260917.log`: original failure and corrected guard pass.
- `tmp/sm5-exact-face-production-v1-20260917.cso` and `.asm`: fresh production exact-face shader.
- `tmp/sm5-pressure-guard-native-v1-20260917-process.json` and `.log`: native replay witness/progress.

## Hydraulic and remaining scene work

The original continuation PID 36872 remains live without restarting.
At 1,950 seconds, state and all 86,720 artificial dry-bank face cells pass.
Maximum depth is 4.370765 m, speed 7.221324 m/s, volume 2,989,620.763433 m3,
maximum step conservation residual 1.309660e-8 m3. Outflow 94.655076 m3/s
still exceeds inflow 45.306955 m3/s: **not settled**, no snapshot promotion.
Reports: `tmp/control-ablation-1950s-state-v1-20260917.json` and
`tmp/control-ablation-1950s-banks-v1-20260917.json`.

The next 2,000-second snapshot also passes both audits: maximum depth
4.346785 m, speed 7.243664 m/s, volume 2,987,138.233310 m3, same maximum
step residual. Outflow 95.235040 versus inflow 45.306955 m3/s remains
unsettled. Reports: `tmp/control-ablation-2000s-state-v1-20260917.json` and
`tmp/control-ablation-2000s-banks-v1-20260917.json`. Next 2,050/local step
5,000 needs both audits after its complete marker. No snapshot promoted.

Remaining: terminal native results, any coupled/full-step corrections, safe
candidate installation and actual play, nonlinear wet-front physics,
source-consistent terrain/boulders/collision, convincing single-surface
breaking waves/froth and 30 FPS. Last ordinary capture remains 28.057157 FPS
/ p95 41.2354 ms, failing the target. Colorado then Pacuare then Futaleufu,
Chilko/Zambezi/all-scene water, crew, normalization and release remain open.
Troublemaker remains a rapid inside South Fork, never a menu scenario.
