# Regional engine state and exact initial burst — September 10

South Fork is still incomplete. Previous regional-partition work was progress;
this pass adds actual engine data consumers and compiled initial-state wiring.
No regional scene is activated or promoted, and no v3 boundary guard is bypassed.

## Implementation

`RaftSimLiquidRegionalState.h/.cpp` adds:

- A canonical ENU-centimetre frame independent of the old fixture's mutable
  geographic translation. Positions/velocities reflect Y once; source positions
  become offsets from the explicit regional origin. A proper positive-scale
  actor basis uses reflected downstream and negated reflected lateral axes.
- Strict parent/region decoders for the prepared schemas. They validate bounds,
  axes, datum, per-axis spacing, extents, particle-volume convention, count/rate
  agreement, finite arrays, source weights and half-open ownership. Failed decode
  clears its output; no truncation or nearest-region fallback.
- Whole-state ownership checks for duplicate/missing regions, cells, seed IDs
  and inlet IDs, plus total external discharge.
- Installation on an unused transient Niagara clone only. An assigned component
  or saved asset is rejected. Initial and inlet arrays, source distribution,
  parent-ID arrays, nominal volume, origin and explicit XYZ allocation are bound.
  Empty inlet arrays stay empty and use zero spawn rate. No artificial internal
  sources are added. Parent IDs are supplied as arrays, **not yet persistent
  cross-region particle attributes or a verified live handoff**.

`RaftSimLiquidInitialState.h` extracts the actual initial-particle reader shared
with the old terrain fixture. It consumes already-framed positions/velocities,
replacing only the initial branch and preserving later inlet spawning. The
legacy caller retains its existing values and behavior.

### Corrected assumption about burst capacity

The previous notes called 163,840 the inherited burst capacity. Inspection of
the **compiled** `Grid3D_FLIP_Tank_Spawn` shows its burst is instead computed from
NX*NY*(water-height-index+oversampling)*particles-per-cell*spawn-multiplier.
It can grow when the regional grid grows. 163,840 is now correctly described as
the retained **seed-table limit**, not an invariant native burst allocation.

Read-only native graph evidence: `liquid-regional-burst-modules.json`.
Regional installation clones that script and substitutes the exact seed count
at the TRUE input of its existing timing gate. It does not replace the output
count unconditionally: the FALSE zero branch, time condition, SpawnInfo and
HasSpawnedThisFrame logic remain. This removes the grid-sized excess allocation
path from the regional CPU spawn program. No cap was increased and no seeds
were removed. Actual runtime regional birth/count validation remains required.

## Verification

- Initial build failed on a collision with Unreal's `FFrame`; renamed the
  explicit type to `FCanonicalFrame`. Subsequent builds succeed.
- First headless test reached the twelve decoded regions, then the test itself
  asserted by inserting an element of a TArray back into that same TArray.
  Corrected it to insert a separate copy. Failed log retained as
  `engine-liquid-regional-state-v1.log`; no completed report from that run.
- `engine-liquid-regional-state-v2/index.json`: two actual-RHI tests pass before
  the exact-count burst change, zero warnings/errors.
- Final `engine-liquid-regional-state-v3/index.json`: **five actual-RHI tests
  pass**, zero warnings/failures, 32.210 s. These include all twelve real region
  decodes, exactly-once ownership, direct comparison of all 719,335 parent seed
  positions/velocities, explicit-frame array bindings, source-fed/zero-inlet/tail
  region shader compilation, exact initial count in the compiled CPU program,
  and fourteen existing coupling variants. They do not run coupled regional
  water or prove regional pressure/renderer continuity.
- The independent SHA256 and exact-row input audit was rerun:
  `liquid-regional-engine-input-audit.json`. It confirms unchanged parent/region
  files, all 719,335 seeds, 6,144 inlet sites and 79,380 XY cells, 17 interfaces,
  47.0068051381853 m3/s external numerical inflow and exact canonical values.
  The C++ in-memory decoder is not a file-signature/provenance verifier; keep
  that paired input audit when loading these prepared files.
- All 197 liquid Python tests pass. Scoped diff whitespace check passes.
- Saved geographic scene SHA256 remains
  `36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

## Actual wet replay

`liquid-regional-reader-regression` runs the existing 68-cell geographic fixture
for twelve seconds after extracting the common initial-state reader. This is
**not** a runtime test of the twelve regions or the exact-count regional burst.

Capture complete, no error. Clock, stage-order, live density, affine transfer
and current-surface foam audits pass: 756 callbacks, 714 positive-clock steps,
30 distinct motion frames, 57,266 final primary particles, max position error
2.290761e-6 m. No engine errors. Existing SimCache volume warning remains.
Blocking capture time 87.821 s is not an FPS measurement. Secondary trajectory
audit was not rerun, so no full secondary-motion acceptance is claimed.

Viewed `terrain_0720.png`: still a glossy/lumpy isolated block with exposed
vertical edges. It does not resemble convincing returning-roller whitewater.
No full-rapid physics, visual or performance acceptance.

## Next integration

Install matching bounded contact tables and distinguish external boundary data
from internal shared pressure/velocity/particle interfaces. Apply each explicit
frame to the actual actor and every query/transport/reconstruction consumer.
Verify regional initial birth counts, wet partial-X pressure execution and
transfer conservation on GPU. Region-specific histories must not share the old
single-fixture render-graph clock/foam state. Then join one visible surface with
raft support, compare full-rapid motion to the real reference and measure
performance. Do not activate all regional volumes on the strength of per-region
capacity checks: aggregate work still needs a measured runtime budget.

No production changes, commit, or goal completion. Later rivers and all other
queued requirements remain in scope.
