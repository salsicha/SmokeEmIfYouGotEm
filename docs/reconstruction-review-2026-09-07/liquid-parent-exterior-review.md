# Parent-domain exterior forcing — 2026-09-10

South Fork remains incomplete. This pass installs the prepared parent-domain
inflow/outlet rules on regional native solvers, without creating reservoirs at
internal cuts. The prepared hydraulic field remains a derived prior, not newly
measured bathymetry or a newly observed discharge.

## Implementation

`RaftSimLiquidParentExterior::FProfile` validates the full physical ownership
partition and parent vector boundary table using the existing regional boundary
builder. Its 2,616 float3 rows are read-only face metadata, not a whole-domain
texture allocation. It retains exact uploaded parent rows and rejects missing
owners, mismatched regional frames/extents and velocities beyond finite native
half precision. The legacy fixed-fixture v3 rejection and per-region allocation
caps remain unchanged.

Optional parent exterior installation on an unused canonical contact clone:

- Opens the four horizontal numerical boundaries and keeps the lower vertical
  numerical face closed.
- Queries the true parent face and tangent column in explicit canonical world
  coordinates, independent of legacy fixture translation. Includes external
  halo corners that lie alongside a neighboring region's portion of the same
  parent face; true parent XY corners are not assigned an arbitrary face.
- Applies the prescribed local-grid vector velocity only to inlet cells above
  the row bed and below its stage; reflects lateral velocity once.
- Classifies outgoing parent cells as pressure outlets and installs their
  kinematic pressure `980 * max(stage - z, 0)` in cm²/s². Regional pressure
  indices are shifted into the parent grid before this query.
- Retains regional pressure ownership, global colors, shared-boundary exchange,
  exact terrain contact and independent bounded allocations. No automatic wet
  activation or particle creation at internal cuts.

## Failures investigated and corrected

The first engine run's one failing test assumed Niagara retained the custom
input name `Position`. The retained compiled code proves it becomes
`In_Position`, with the exact canonical reflection intact. The test now checks
the exact expression in its owned graph plus actual compiled table consumers;
final logs retain the compiler expression. This was not a hydraulic relaxation.

The first native inflow audit found 694 tuple mismatches, generally one half-float
step, while all 6,720 outlet pressures passed. Explicit `f32tof16` conversion
did not fix those same mismatches (`liquid-parent-exterior-v2`). An explicit
nearest-even half lattice, using exact exponent bits and a subnormal quantum
floor, resolved them (`v3`). Do not attribute a more specific driver/compiler
cause than this evidence establishes. No inflow comparison tolerance was raised.

## Final evidence

- Build32507 succeeds. `engine-liquid-parent-exterior-v3/index.json`: four engine
  tests pass, no warnings/failures, 13.622 seconds. Covers native GPU compilation
  for three regional exterior configurations, contact/projection regression,
  exact boundary exchange, pressure coloring, missing-owner rejection, parent
  mismatch rejection, unchanged face-table bytes and half-overflow rejection.
- `liquid-parent-exterior-v3`: all twelve actual native regions; 1,414 aligned
  groups, 27 boundary exchanges, 1,080 pressure exchanges, no incomplete or
  misaligned groups/errors. Native compiled shader retained as
  `region-004-native.hlsl`.
- `exterior_audit.json`: **898 prescribed inlet cells** have exact expected
  nearest-half velocity/type; **6,720 outlet cells** have correct type/pressure.
  No unexpected outlet cells, unforced velocities or unprescribed pressure in
  any region, including internal edges. Parent face selection is reconstructed
  independently from global cell indices, not copied from shader decisions.
  Pressure comparison bounds two float32 height ULPs per operand times gravity
  for GPU FMA/reference-rounding differences; this bound was specified before
  readback, not tuned to fit it. Observed maximum error is at most 0.063 cm²/s².
- `boundary_audit.json`: all 5,960 shared columns / 143,040 complete boundary
  tuples still match physical owners exactly.
- `contact_audit.json`: 1,587,600 physical non-border classifications still match
  the captured terrain triangles exactly.
- 224 Python liquid tests pass, including opposite lateral velocity, wrong
  pressure/type, internal spurious reservoirs/forces, and partial/nonfinite data.
  Scoped `git diff --check` passes.

The native run has ZERO particles and ZERO source emission. Its 23.437 seconds
is blocking capture/readback wall time, not gameplay FPS. These checks establish
boundary behavior, **not wet discharge conservation, wet pressure convergence,
whitewater appearance, raft interaction or performance acceptance**. The prior
isolated wet fixture remains visually rejected; no replacement screenshot or
photorealism claim is made from empty-grid diagnostics.

## Next work

Implement conservative inter-region P2G before normalization and particle
ownership handoff, then current velocity synchronization / connected wet pressure
tests and continuous live surface/foam. The retained native shader shows the
existing neighbor-query rasterizer accumulates velocity and TotalWeight, then
normalizes inside that function. Copying already-normalized velocities cannot
replace summing raw weighted momentum and weight from all contributors.

Then validate actual full-rapid water/raft motion, compare moving renders with
real references, measure gameplay performance and finish the complete queue.
Colorado, Pacuare, Futaleufu, other water scenes, crew, normalization and release
work are unchanged in scope.

All owned handles are terminal, including final build32507, native76433 and
engine86102. Earlier failed/diagnostic artifacts are retained. Saved geographic
map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No saved map promotion, commit or push. Full goal stays active.
