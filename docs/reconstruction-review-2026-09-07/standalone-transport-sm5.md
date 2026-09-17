# Standalone SM5 transport qualification — pending

2026-09-17 UTC. The [full-face correction](shoreline-validation-and-full-face-sm5.md)
passes isolated exact arithmetic, but that does not qualify reconstructed fluxes,
pressure forcing or an evolved step. This runner extends the check to the actual
six-phase transport pipeline. Compilation is live; **no full transport pass is
claimed**. Production shaders, installed modules, geometry and gameplay remain
unchanged. The full project goal remains open.

## What is implemented

`physics/tests/transport_gpu_control.cpp` compiles and executes the production
`RaftSimTotalDepthTransport.usf` through D3DCompiler/D3D11 SM5, on hardware or WARP.
It supports the original binary, continuous and unscaled fixture versions as
explicit selections; only the unscaled candidate is currently compiling.

The original function body and arithmetic helpers are retained. An include
handler supplies the explicitly selected local exact-hydrostatic header and
omits the engine platform include, whose macros this standalone shader does not
use. The entry point is wrapped only to write a separate phase/model identity
tag. No rate, wet graph, expected state or CPU pressure result is uploaded as a
replacement for GPU computation. Resource slots and constant offsets come from
the compiled bytecode's reflection, not guessed bindings.

Six ordered dispatches match native transport: input/geometry preparation, raw
slopes, reconstruction selection, face fluxes, conservative rate/group peaks,
then CFL reduction. Each producer UAV is unbound before its consumer SRV.
The runner checks each phase/model tag, complete fixture consumption, original
wet-graph equality, geometry equality, bed slopes, rate norms, exact rest/zero
foam, closed-domain mass conservation, diagnostics and CFL. Rate/slope gates
remain relative<2e-5 and max<1e-3, mass residual<=2e-6 times mass-rate magnitude,
and the native CFL relative gate<2e-5 without a new floor.

The fixture's pressure expectations/fractions are consumed but are **not**
pressure validation: this runner does not dispatch the nonlinear pressure solve,
RK2 acceptance/clock update, moving owner, prescribed exterior trace or render
path. Its output explicitly states `pressure_or_step_accepted=0`. It cannot close
the original engine suite or justify a playable physics promotion.

The C++ executable builds successfully with MSVC and d3d11/d3dcompiler/dxguid.
Initial Windows min/max macro and missing reflection-identifier library errors
were corrected before the successful build. Two CLI rejection checks pass:
invalid invocation, and invalid model version before any output creation.
Thirteen actual-execution pytest cases collect successfully but have **not run**:
both original-fixture backends, malformed input, four native invalid physical
states, and compiled-model mismatch. Unconfigured hosts skip; skips are not passes.

## Exact live compilation — preserve, do not restart

Session40945 / PID8220, start UTC `2026-09-17T02:32:50.7234592Z`, is still live
with advancing CPU. Phases0,1,2 compiled; phase3 is still compiling. No timeout
or incomplete output is treated as terminal. Phases4/5 and all runtime comparisons
remain pending. The first three bytecode sizes are11032,15724,2000 bytes.

Executable `tmp/sm5-transport-control-v1-20260917.exe`, SHA256
`7d2dfb8a20cced1af7f81d1952ffa9a787f3ffcc3a2172d721b9be53b66138ea`.
Output directory `tmp/sm5-transport-unscaled-candidate-v1-20260917` retains .cso
and warning/error .log files per phase. Full command, process identity and input
hashes are in `tmp/sm5-transport-unscaled-candidate-v1-20260917-process.json`.
The local exact-header candidate remains SHA256
`521b50bac053ebebe1c6fe52ee39b96ede91fd76c85d5a7181f62d6211e987e0`.

After this SAME process completes, run:

```text
tmp/sm5-transport-control-v1-20260917.exe run tmp/sm5-transport-unscaled-candidate-v1-20260917 tmp/south-fork-unscaled-transport-fixtures-v1-20260914.bin hardware
tmp/sm5-transport-control-v1-20260917.exe run tmp/sm5-transport-unscaled-candidate-v1-20260917 tmp/south-fork-unscaled-transport-fixtures-v1-20260914.bin warp
```

Then configure RAFTSIM_TRANSPORT_CONTROL_EXE, RAFTSIM_TRANSPORT_CONTROL_SHADERS
and RAFTSIM_TRANSPORT_CONTROL_FIXTURE for
`physics/tests/test_transport_gpu_control.py`. Keep failures and compiler warnings;
do not weaken original comparison gates or report a prefix as a complete pass.

The original engine replay9319/PID9976 and workers31736/36256 are also still
live. Their63 witnessed shader inputs and installed modules remain frozen.
The standalone candidate is not a restart or replacement for that engine job.
Do not change either compiler's actual input files while it is running.

## Original hydraulic continuation

Same cook40601/PID11316 completed1750s/local23000. State and all86,720 artificial
bank-face cells pass exact-dry checks. Maximum depth4.456683m, speed7.174340m/s,
volume2,999,176.744439m3; max step conservation residual1.707900e-8m3.
Outflow91.271027 versus inflow45.306955m3/s: **not settled**, no promotion.

- `tmp/control-ablation-1750s-state-v1-20260917.json`, SHA256
  `8d6c0189d8e552abda9adc03e02bad6eb1c86eef25223b3c2f7ef78fa7ae1472`.
- `tmp/control-ablation-1750s-banks-v1-20260917.json`, SHA256
  `8bd4d57c3eebb71c97478eca742f96b76308d46905a082ee523411988f32dec9`.

Next complete1800/local24000 requires both audits and the original process's
terminal result. No transient state is promoted solely because the cook ends.

The pressure wetting-edge discontinuity is a separate model defect: the existing
reconstructed/source-supported candidates still lack qualified finite-time
wet-front evolution. Arithmetic/transport diagnostics do not fix that force jump.
Do not hide it by disabling pressure, closing real wet connections, adding depth
floors or changing source geometry. Last ordinary performance remains27.068531FPS
/p9543.391ms, FAIL30. Shared nonlinear water/contact/crest/froth integration,
evidence-consistent terrain/boulders/collision, normal installation,30FPS, source
closure/normalization, Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi/all-scene
water, crew and release remain open. Troublemaker remains only a South Fork rapid.
