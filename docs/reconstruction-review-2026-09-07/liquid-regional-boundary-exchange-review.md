# Shared regional boundary exchange — 2026-09-10

South Fork is still incomplete. This pass follows the verified regional pressure
phase/ownership work and implements another required part of a connected solve.
It is not evidence of realistic moving water or completed scenes.

## Implemented

The GPU halo primitive now has separate typed entry points for scalar R32F
pressure and native RGBA16F `SolidVelocity_Boundary`. Both reuse the audited
physical-owner map and single-pass, disjoint-source/destination scheduling. The
boundary version copies all four components exactly: solid velocity XYZ and
boundary type W. It does not average cell types, normalize velocities, reduce
P2G contributions or transfer particles.

The regional native coordinator invokes boundary exchange after the complete,
aligned **Compute Boundary** dispatch group, before the next native velocity
extrapolation/divergence/pressure stages. Native tracked RDG textures supply the
ordering; this is not a previous-frame copy. The same graph-local map is reused
for subsequent per-iteration pressure exchange. Physical owners are unchanged;
shared edge and diagonal/corner halos receive the actual owning cells' values.

The opt-in `-RaftSimRegionalBoundaryExchange` probe requires canonical regional
contact and compatible projection. It still has zero particles and zero inlet
emission. Wet operation is deliberately not enabled while conservative grid and
particle exchange are absent.

## Verification

- Build 94097 succeeds. Actual GPU tests in
  `engine-liquid-boundary-halo-v1/index.json`: three pass, zero warnings/failures,
  6.929 seconds. Includes a 16-owner RGBA16F test with different grid dimensions,
  opposite exchanges and corner destinations, all four boundary types and signed
  velocities. A second same-graph update changes owner zero; complete volume
  readbacks match exactly, including unchanged physical cells. Wrong texture
  formats and aliased owners are rejected. Existing scalar pressure exchange and
  regional canonical contact/projection compilation regressions also pass.
- `liquid-regional-boundary-exchange-v1`: all twelve actual native regions,
  1,518 aligned groups, 29 boundary exchanges and 1,160 pressure exchanges. No
  missing/misaligned groups or exchange errors; all runtime addresses match the
  independently prepared geometry. Every native Compute Boundary group has one
  exchange before downstream work.
- `boundary_audit.json`: all **5,960 columns / 143,040 cells** exactly match the
  current physical owner in all four half-float components, with zero tolerance.
  The audit reconstructs addresses from the independent canonical ownership
  pages and reflects Y on both ends. It does not accept exported C++ expected
  values as proof.
- `contact_audit.json`: all 1,587,600 non-border physical terrain classifications
  still match captured triangles exactly.
- `pressure_marker_audit.json`: all 2,113,056 first-color nonzero pressure values
  still match, so boundary exchange did not regress global pressure colors or
  shared pressure protection.
- 219 Python liquid tests pass, including stale boundary type, a wrong velocity
  component, duplicate writes, nonphysical sources/destinations and invalid data.
  Scoped `git diff --check` passes.

The native capture's 19.832 seconds is blocking diagnostic wall time, **not FPS**.
The empty native run proves boundary tuple synchronization, not wet mass/momentum
conservation, wet pressure convergence, exterior forcing or visual acceptance.
The 16-owner GPU unit test includes fluid/outlet types, but does not simulate a
river and must not be represented as one.

## Next integration

1. Explicit exterior inflow/outlet-stage rules. The regional shared masks are now
   imported, but the inherited numerical exterior boundary settings are still
   not the full river's forcing. Do not turn internal cuts into reservoirs.
2. Conservative P2G mass/momentum exchange before normalization, followed by
   particle ownership handoff without creation/deletion at regional interfaces.
3. Current velocity synchronization in the native D/P/G sequence, connected wet
   pressure validation and mass/flux/contact tests.
4. Shared continuous surface/foam, full-rapid motion, raft interactions, real
   footage comparisons and actual gameplay performance. The previously viewed
   isolated wet fixture is still glossy/lumpy and visually rejected.

A possible implementation route for exterior forcing is a dedicated read-only
parent boundary table, validated against the full ownership partition: use the
parent physical face/column, not a region's internal edge. This is not implemented
in this pass. Keep the legacy fixed-fixture v3 rejection and allocation caps;
do not use acceptance of a large table to allocate an unbounded whole-domain grid.

All owned handles are terminal: build94097, engine5049, native64303. No editor or
build process remains. Saved geographic map SHA256 is unchanged:
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No map promotion, commit or push. The entire queue and goal remain active.
