# Regional raw momentum/volume transfer — 2026-09-10

South Fork remains incomplete. This is native solver integration and numerical
GPU evidence, **not wet cross-region conservation, appearance, or performance
acceptance**. No scene or saved Niagara system was replaced.

## Implemented

The owned native NQ rasterizer now publishes a named `Momentum_Volume` RGBA32F
grid before dividing by local weight. Its xyz values are summed kernel-weighted
particle volume times grid-local velocity (m³·cm/s); w is summed weighted volume
(m³). The common water density cancels when recovering velocity. Each invocation
writes empty cells too. Both native raster branches are patched, while the active
regional branch retains the complete centered, rotated-metric tent gather.

`Emitter.RiverRawTransfer` is an emitter-spawn default DI, not a user-parameter
DI. Actual initialization exposed why the first version could compile yet fail:
Niagara clones a user DI beneath the component, but Grid3DCollection's
`FindAttributes` needs a NiagaraSystem owner and its execution-ready DI identity.
The user clone had an empty attribute list. The emitter-owned binding is now
verified against actual single-attribute, untiled RGBA32F runtime storage.
Native grids receive dimensions during initialization; their render-thread
dimensions are checked at every transfer stage, not assumed from pre-tick values.

`RaftSimLiquidTransferGPU` reverses the validated physical-owner-to-halo map.
Each unique physical column gathers its own deposit and every distinct subscriber
deposit, including diagonal/corner contributors, in deterministic owner order.
It writes the same total to that physical column and all its halos. Input
textures are immutable and output totals are separate, preventing read/write
races or accidental reuse of already-reduced mass. Unshared and exterior cells
are copied unchanged. Allocation, duplicate address/contributor, format, and
alias checks reject invalid inputs.

The opt-in `-RaftSimRegionalTransfer` coordinator runs after **all** matching
`Neighbor Grid Rasterize Particles` dispatches finish. It reduces deposits,
normalizes once, and replaces native `Velocity` and `SimFloat` support before
`Compute Boundary`. Terrain/exterior classification and the existing D/P/G
pipeline run afterwards. Positive volume is not dropped by an arbitrary support
threshold; empty cells clear velocity/type explicitly. Raw momentum remains
full precision even though the current native velocity output is RGBA16F.

## Verified evidence

- Build succeeded; final build handle 91265. No engine/build process remains.
- `engine-liquid-raw-transfer-v8/index.json`: **5 succeeded, zero warnings,
  zero failures**, 17.14 seconds of test time. Native regional contact/exterior
  compilation, existing boundary exchange, raw reduction, and resolve tests.
- The reduction GPU test checks all voxels in 16 differently sized owner grids,
  bidirectional faces, a four-region corner, zero local support, signed raw
  momentum exceeding half range, changed input on a second same-graph pass,
  unchanged input deposits, exact totals, and invalid map/alias/format rejection.
- The resolve GPU test verifies exact native velocities and support for zero,
  very small positive, ordinary, and large volumes. Empty outputs overwrite
  stale values, and large raw momentum does not overflow before division.
- `liquid-regional-transfer-v4/capture.json` and `stages.json`: all 12 actual
  regions, **1,518 aligned groups, zero incomplete/misaligned groups, 30 raw
  reductions/resolves, 1,160 pressure exchanges, 29 boundary exchanges**.
  Every one of 5,960 shared map addresses matches the independently prepared
  canonical ownership map. Actual transfer DI formats and post-stage dimensions
  are checked. This run explicitly has **zero primary particles and no source
  emission**. Its 30.51-second blocking capture time is not a frame-rate result.
- Independent readback audits in that directory still verify 898 prescribed
  inlet velocity cells, 6,720 outlet pressure cells, all 143,040 shared boundary
  cells (exact), and 1,587,600 physical terrain classifications (exact).
- Existing Python liquid suite: **224 tests passed**.
- Saved `SouthForkRegisteredRockPlayable.umap` SHA256 remains
  `36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

Earlier failed runs are retained: global shader parameter declarations/resource
arrays (engine v1/v2), custom pin assumptions and the single-bin threshold variant
(v3/v4/v6), graph mutation during UObject hash iteration (v5), and the user-DI
runtime ownership issue (native v1–v3). The successful final tests use the
corrected code; no gate was loosened to call those failures passes.

## Still required — next work

1. Follow-up: [native packet evidence](liquid-native-transfer-review.md) now
   verifies actual four-particle P2G at a shared corner on steps 1 and 3, after
   fixing missing spawn insertion and inherited fixture-volume deletion. This
   is not dense NQ capacity, sustained flow, or full-rapid conservation evidence.
2. Same-step particle ownership handoff, retaining identities, position,
   velocity/affine state and volume without duplicated emission or dropped
   particles. Current raw reduction assumes unique ownership and a common
   frame/metric; it does not implement migration when particles cross a region.
3. Connected wet pressure/G2P tests, boundary flux accounting and native velocity
   range/precision validation; shared surface/foam and secondary-water ownership.
4. Actual full-rapid water/raft/collision/shoreline captures and motion, comparison
   against the real reference, and an uninstrumented performance run. Then the
   rest of the original river/crew/cleanup/release queue and final commit.

All handles are terminal, including native 94442 and engine 57068. No commit or
push was made. The full goal remains active.
