# Owner-scoped reconstruction and rectangular metrics — 2026-09-10

South Fork remains incomplete. The prior regional-geometry pass was progress.
This pass removes two concrete single-fixture assumptions needed before live
regional integration: render-graph-global histories and hard-coded square
reconstruction geometry. It does not install a coupled regional fluid solve.

## Changes

`RaftSimLiquidGraphHistory.h` stores clock, foam and within-graph step count per
attachment generation. Every live reconstruction attachment gets a fresh
monotonic ID, even if a Niagara system is reused. Intermediate same-graph foam
is reused only by that attachment. Entries have stable storage across map growth;
RDG references are not carried into a new graph. Cross-graph history remains in
the existing owner-held pooled resource. `RaftSimEditorLiquidLiveDensity.cpp`
uses this registry in the actual pre-secondary and post-render callbacks.

`RaftSimLiquidReconstructionLayout.h` replaces the square constants in live
grid/texture validation, density, distance reconstruction, foam and readback.
It uses the explicitly installed allocation cells and world grid extent from the
system's exposed parameters, retaining the old layout for old fixtures without
an explicit allocation. Solver/render alignment, two-cell XY halos, even X and
the unchanged two-million-render-voxel cap are checked. It does not infer a
rectangular allocation from a max-axis count. Component overrides and dynamic
live changes to these parameters are not a supported configuration path here.

The footprint/radius model is retained, not physically recalibrated for the
regional nominal particle volume. The old origin-LWC-tile restriction remains.
No regional coordinate transform or pressure exchange is silently added.

The foam GPU API now accepts independent X/Y physical half-extents. Existing
square callers have a compatibility overload. Its source taper uses the nearest
physical side of the rectangle. This remains the external-edge policy: shared
interface foam/history exchange and disabling artificial internal-edge taper
must be integrated with the coupled solve, not assumed complete here.

Live diagnostic reports include explicit solver cells, render cells, extents,
minimum and owner-history identity. Python live-density/current-foam audits now
read these dimensions through a strict layout decoder, and the independent foam
reference accepts rectangular physical extents. Old reports remain supported;
partial, odd, oversized, or inconsistent 2x layouts are rejected.

The existing console diagnostic still permits only one active fixture attachment.
The owner-scoped registry is exercised with interleaved GPU owners in a test,
not by claiming twelve connected Niagara systems are already running.

## Verification

Build95174 succeeded with two test-literal conversion warnings; corrected both.
Build9676 succeeded without those warnings. Build11206 succeeded after adding
explicit rectangular-edge GPU cases. 207 liquid Python tests pass.

Actual D3D12/RHI-validation report `engine-liquid-reconstruction-owners-v2`:
four successes, zero warnings/failures, 4.970 s. Earlier v1 also passed, before
the additional rectangular-edge cases. Tests:

- `LiquidReconstructionOwnersGPU`: two differently shaped volumes interleaved
  in one real render graph; A advances twice, B is paused, new C resets cleanly.
  Checks every output texel, independent clocks/metadata and step counts,
  pending same-graph history, stable references through registry growth, and
  empty RDG references in a subsequent graph. This is not live Niagara pressure
  or mass transport between owners.
- `LiquidReconstructionLayout`: actual 110x38x24 tail layout becomes
  220x76x48 with physical half-extents 2650x850 cm; rejects odd, truncated,
  oversized and empty-physical layouts without partially replacing valid state.
- `LiquidFixtureCurrentFoamGPU`: seventeen actual-GPU cases. The new cases
  independently test narrow-X and narrow-Y source taper; all existing transport,
  pause/reset/decay/solid and affine/non-affine precision cases retained.
- `LiquidRegionalGeometry`: all twelve prepared boundary/contact mappings still
  agree with the engine builder.

Saved geographic map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No production assets promoted or commit made.

Actual twelve-second replay `liquid-reconstruction-owners-regression` completes
with the owner-scoped live callback and explicit legacy metric report. Core
clock/stage/live/affine/current-foam audits pass: 759 callbacks, 714 positive
steps, 45 render-only callbacks, 30 distinct decoded motion images, 57,287
primary particles, 56,007 supported. Maximum position error 2.163714e-6 m;
affine moment error 3.779895e-6 /s. Active foam reference coverage error is
0.00048828125 and paused coverage is exactly preserved. No engine errors;
existing Niagara SimCache material-DI warnings remain. Blocking capture time
86.000 s is NOT a frame-rate measurement. Secondary trajectory validation was
not rerun (54,287 secondary particles reported).

Viewed `terrain_0720.png` still shows a glossy/lumpy isolated water block with
exposed vertical sides. This fails the visual requirement; no actual multi-region
fluid or performance acceptance. The replay uses the old square fixture, not
the newly supported rectangular regional live reconstruction. The separate GPU
history test uses rectangular volumes but no Niagara physics exchange.

All owned sessions are terminal: build95174, build9676, test97586 (v1),
build11206, test84171 (v2), wet57759. The read-only broad header search9955 was
stopped after locating its typedef. Scoped git whitespace check passes.

## Remaining integration

Install explicit regional frames and terrain/boundary bindings; coordinate
pressure iterations and conservative particle/grid exchange; include shared
foam/reconstruction support without seams, duplicate surfaces or internal
reservoirs. Validate actual regional birth, v3 contacts, partial-X wet behavior,
the raft and full-rapid footage/performance. The queue remains South Fork first,
then Colorado, Pacuare, Futaleufu and the remaining all-scene/crew/cleanup work.
