# Retained native South Fork interface — September 11

Status: implemented and verified as an optional, unsaved live transport layer.
It is not yet connected to pressure classification or the visible renderer.
South Fork and the complete reconstruction queue remain incomplete.

## Implementation

`-RaftSimRegionalInterfaceTransport` uses the actual twelve-owner reservoir-v1
river, original particle source, registered contact geometry, shared momentum,
pressure projection and compact particle transfers. It loads the hash-checked
initial explicit interface prepared in `tmp/south-fork-liquid-interface-20260911`.
Each owner retains an R32 scalar between native steps. After Project Pressure,
RK2 transport samples that step's native velocity and exchanges internal scalar
halos. Multiple native steps in one render graph use the newest graph-local
scalar rather than re-registering the previous frame's pooled texture.

The timestep comes from the immutable native GPU tick's external parameter
bytes, at the initialized layout offset for
`Grid3D_FLIP_FluidControl_Emitter.DeltaTime`. Engine global delta is recorded
separately from that same tick. Neither clock is inferred from wall time or the
Python runner's requested timestep. All owners must agree. Every transported
step retains updated-cell, invalid-trace and nonfinite counts. The selected
step saves both the pre-transport and post-transport scalar alongside its
existing native post-pressure velocity packet.

The first native step is a reset/spawn step and does not execute Project
Pressure. Exactly one initial reset is required; transport is consecutive from
native step two. The independent auditor checks the actual stage journal,
including any later ticks enqueued before the game thread notices packet
readiness. Those later ticks do not replace the selected paired packet.

## Startup failures and corrections

- The initial attempt used the unqualified `Emitter.DeltaTime` name; native
  layout inspection exposed the emitter-qualified name.
- The v2 attempt still failed before any flow step: `ExternalCBufferLayoutSize`
  is zero until the first emitter Tick, even though Activate has initialized
  the source parameter layout. The early check now uses the source byte-array
  size. The runtime callback still validates against the immutable tick size.
  This follows UE's `NiagaraEmitterInstanceImpl.cpp` and
  `NiagaraComputeExecutionContext.cpp`, not a removed bounds check.
- v3 reached flow but rejected step two because transport incorrectly expected
  a Project Pressure update during reset. The actual captured stage journal
  demonstrated the missing reset-stage projection. Explicit initialization and
  transport counters fix that distinction; no fabricated zero-time update.

Builds 23392, 20854 and 45471 all succeeded (31.76, 33.48 and 31.06 seconds).
Native v3 session 21490 exited zero but its capture failed and is not a pass.

## Actual river evidence

| Capture | Selected native step | Real transport updates | Elapsed fluid seconds | Maximum final-step CPU/GPU scalar difference |
| --- | ---: | ---: | ---: | ---: |
| `liquid-native-interface-startup-v4` | 12 | 11 | 0.1833333429 | 0.000526833 cm |
| `liquid-native-interface-600` | 600 | 599 | 9.9833338540 | 0.000621733 cm |

Both native runs completed with empty exchange errors and RHI validation
enabled (sessions 6439 and 88635, terminal zero). Their `interface-audit.json`
files independently reconstruct the selected RK2 step and every internal halo
copy. Each comparison covers 2,178,720 samples. The longer run's diagnostic
ledger verifies 982,407,920 owned-cell updates over all 599 transports, with
zero rejected traces/nonfinite samples. Its retained pre-step scalar differs
from initialization at 295,459 samples, so this is persistent motion, not a
reinitialized field. Both actual fluid and engine deltas were
0.01666666753590107 seconds throughout these runs.

Full native particle/P2G audits passed independently:

- Step 12: 729,558 particles; zero shared reduction mismatches; no survey versus
  prepared-float internal storage-cut differences.
- Step 600: 701,412 particles; zero shared reduction mismatches; two internal
  storage-cut differences between survey-double coordinates and the independently
  reconstructed native float frame. Actual exterior bounds remain unchanged.

The long capture's `flow-budget.json` verifies all 598 compact transfers through
step 599, 22,496 births and 50,845 approved exits. Nominal storage still falls
590.6041667 cubic metres over those transfers. This is **not steady-flow or
physical acceptance**, and the optional interface has not changed pressure.

399 Python liquid tests pass. Engine session 54564 completed 20 tests with zero
failures: 19 clean successes and one success with a Google connectivity timeout
warning in LiquidRegionalExterior. Report: `liquid-interface-live-engine/index.json`.
No engine/build process remained after the checks. These runs do not establish
playable FPS or visual quality; their offscreen capture only drives simulation.

## Remaining work, not bypassed

The outer XY halos and two Z edge layers still retain provisional initial
values. Initial surface coverage still misses 64 prepared particles, as recorded
in the preceding review. The scalar is not a signed-distance field. Correct
particle-supported surface coverage and boundary evolution before using it as
the authoritative pressure/render surface. The pressure solve must use the
pre-transport interface for that step; visual reconstruction must use the
post-transport state with correspondingly advanced particles, not the earlier
P2G particle packet. No second water surface should be added.

Next: implement consistent current-interface phase/subcell pressure and particle
correction, preserve strict signed boundary/backflow checks, then inspect actual
rendered motion, foam, shoreline and runtime cost. The previous long-run failure
at native step 641 is not resolved by this ten-second transport proof.

The saved South Fork review map is unchanged, SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No production promotion, scene completion, commit or push in this pass.
