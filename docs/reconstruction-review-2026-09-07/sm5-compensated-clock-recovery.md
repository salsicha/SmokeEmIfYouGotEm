# Native compensated-clock recovery

2026-09-17 UTC. The original long-running native replay is terminal, not hung
or waiting. This correction recovers27 native regression tests. It does not
finish South Fork physical/visual/performance acceptance.

## Original terminal evidence

Session55459/editor36412 finished with engine exit0, but its authoritative
33-test report contains **5 PASS / 28 FAIL**, no unrun/in-progress tests.
The wrapper therefore exits1 correctly. Worker37836 completed; the earlier
7200-second hung-shadermap message was not a terminal event. Do not restart or
continue polling these old handles. Their63-shader freeze ended with the run.

Passing: NonlinearAccelerationGPU, NonlinearPressureGPU,
PressureResidualQualificationGPU, RepresentedFloatArithmeticGPU and
TotalDepthTransportGPU. The remaining failures included clocks, step/interval
transactions, observations, breaking-front integration and prescribed inlet
positions. Original unscaled transport and exact-face fixtures were retained.

- Report `tmp/sm5-pressure-guard-native-v1-20260917/index.json`, SHA256
  `73f449826e948d827ac4c767f8bc360585f5986ee501b5ed03734c5e1ddc9a94`.
- Log `tmp/sm5-pressure-guard-native-v1-20260917.log`, SHA256
  `4379ed3a2ff72eece4d025e1d2d498e95c789a6d1258a9addbf655b942ec2930`.

## Observed clock failure and correction

Native step case0 proposed a valid0.00100000005s step at1048576s, but returned
the unchanged high/low pair `(1048576,0)`, diagnostics `0/0/16/0`, and rejected
the step. A hybrid step at3.125s accepted state but lost its clock residual
7.25267454982e-8s. Temporal retries also lost their previous low word.

`RaftSimPortableClock.ush` implements the same error-free TwoSum normalization
and compensated advance, using the already-qualified integer-rounded FP32
add/sub helpers for each operation. Step endpoint subtraction and interval
normalization use the same helper. No clock reset, endpoint snap, larger
tolerance, altered dt ceiling, state repair, or relaxed rejection gate occurs.
Only the two clock-using shaders and the new helper differ between native runs.
No C++ module or physical reference fixture changed.

An independent standalone D3D11 harness executes the actual production step
phase4 and checks all12 output words: clock/progress, step info and diagnostics.
Its26 cases cover large clocks, noncanonical equivalent encodings, both signs,
small final intervals, explicit observation endpoints, overflow and rejected
trials. Expected clock sums/residuals use rational arithmetic in the test.
Malformed-fixture and final-word negative controls are also exercised.

Both direct-FXC baseline and corrected phase4 pass all six harness tests on
hardware/WARP. Thus the isolated baseline **does not reproduce the native
failure**. Unreal has additional shader preprocessing paths, but the specific
transformation responsible remains unproven. Do not claim the harness proved
a driver bug or promote its baseline pass to native acceptance.

- Baseline bytecode `tmp/sm5-clock-baseline-v1-20260917.cso`, SHA256
  `a81745dff2f10bd0bc54ae121d31968f3f66e65a0a1743302f644fba98840468`.
- Corrected bytecode `tmp/sm5-clock-portable-v1-20260917.cso`, SHA256
  `2f65abf713b0534dfd55cb9cd68fb8707655a685f5010961db993e5860e01d91`.
- Baseline JUnit `tmp/sm5-clock-baseline-v1-20260917.xml`, SHA256
  `b2e80f44b15b29e57e03bec334fdb7af2e3260908ee9989e681803cd2649b2d8`.
- Corrected JUnit `tmp/sm5-clock-portable-v1-20260917.xml`, SHA256
  `3b8d76dc0c0532d0c02f1948c897343092c17c8ce3104944e546212c45f772e7`.

The first harness launch lacked pytest on PYTHONPATH; no tests ran. It was
rerun with the existing dependency paths. Compilation retains the existing FXC
loop-variable warning; this is not warning-clean release-build acceptance.

## Native A/B result

Session43990/editor36668, start2026-09-17T06:50:15.5120557Z, is also terminal.
Same33 tests and byte-identical original fixtures: **32 PASS / 1 FAIL**.
All64 candidate shader hashes verified at completion. The five earlier passes
remain passes and27 former failures recover. The wrapper exits1 because the
remaining failure is real, despite engine exit0. No live shader freeze remains.

Native step case0 now accepts with diagnostics `0/0/0/1` and clock
`1048576+0.00100000005`. The hybrid clock retains its full residual and has
zero measured time error. Temporal evolution completes in two accepted trials;
component-relative errors are at most4.58720314467e-8, maximum state error
9.53674316406e-7, within the unchanged gates. Split/chained interval and
indirect/direct execution checks pass. Boundary mass residual1.08875084312e-6
is still reported as float-storage roundoff, not repaired.

Remaining failure: `RaftSim.Editor.LiquidPrescribedNormalGPU`, cases44 and56.
Their printed three-decimal coordinates conceal the exact-bit mismatch.
The independent CPU inward-position oracle and original assertions remain
unchanged. Inspect higher-precision output/exact projection before correcting
the shader; do not relax position or exit-classification tolerances.

Report `tmp/sm5-portable-clock-native-v1-20260917/index.json`, SHA256
`6f5ba527730bdecebae99964c6d4e29d99657e894af8d4a1f50bf10db810e0c3`.
Witness and log share that prefix (`-process.json`, `.log`).

Combined standalone regression: **60 PASS**,76.30s, no failures or skips.
Fresh corrected clock bytecode plus the previously qualified unchanged
transport/pressure/arithmetic artifacts cover original unscaled transport,
coupled pressure, activity guards, exact arithmetic and resource bindings on
hardware/WARP. This does not replace the native A/B or qualify scene FPS.
JUnit `tmp/sm5-portable-clock-regression-v1-20260917.xml`, SHA256
`e0c84bb976d96be5f8fcee3e60772ff3c53bda172c3ecf573bc773994abf8891`.

## Hydraulic continuation and full remaining scope

Same cook51728/PID36872 remains LIVE. At2450s/local13000, state and all86,720
exact-dry artificial-bank checks PASS on5,382,400 cells. Maximum depth
4.1527782930m, speed6.5193068347m/s, volume2,964,303.359677826m3 and maximum
step mass residual1.6470207420e-8m3. Outflow96.1114277733m3/s versus
inflow45.3069545472m3/s: **NOT settled or promoted**. Next2500/local14000
requires both audits after its completion marker.

- State `tmp/control-ablation-2450s-state-v1-20260917.json`, SHA256
  `40b372119cb35ba5ebd8d3496f38d04a2922c3b26e22af5681626f75cc339f52`.
- Banks `tmp/control-ablation-2450s-banks-v1-20260917.json`, SHA256
  `843f602e104cbe30c1faf44a4adc724343a5999d2fd428fa9d3d3bd8099f11bd`.

Native test recovery is not full nonlinear wet-front physics, actual playable
engine motion/reference comparison, or terrain/boulder/collision acceptance.
The conditional lateral front still needs ownership, energy, finite-time and
bed/pressure/curvature coupling. No scene FPS rerun or visible-water acceptance
is claimed: last28.057157FPS/p9541.2354ms still FAILS30. South Fork wave/froth
integration, Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi/all-scene water,
crew, normalization/regressions and release remain OPEN. Troublemaker remains
only a rapid within South Fork, not a menu scenario.
