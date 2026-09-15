# Exact source fragments before coordinate rounding

September 14, 2026. Geometry representation progress, **not evolving solver,
native water, visual or 30 FPS acceptance**. The original failing tests remain.

## Why the old vertex API cannot carry every clipped fragment

The existing storage/face equality test still finds a 1.7764e-15 discrepancy
between independently rounded storage polygons and canonical source-face cuts.
Replacing only the clipping arithmetic previously exposed a second problem:
positive exact fragments can become degenerate when their vertices are exported
to float coordinates. Removing such triangles would discard source area.

`subcell_exact_geometry.py` now retains immutable rational source polygons,
original source IDs and original affine bed gradients. Clipping predicates,
triangulated projected areas and four hydrostatic depth moments are evaluated
before any coordinate round trip. Only exact duplicates and zero-area pieces
are removed. Cell coverage must equal the requested rational rectangle area
exactly, without an area tolerance, welding or terrain displacement.

These rationals represent the supplied binary coordinates exactly; they do not
improve the measurement accuracy of captured or inferred terrain. Original
source IDs preserve access to the existing mixed vertex-authority records.

The affine synthetic case at center (0.1,-0.1), spacing (1.2,0.8) includes
positive fragments whose float projected area is zero. Tests retain their
positive exact areas, storage and original slopes. Independent analytic ramp
integrals, exact source subdivision, original face cuts and datum-relative
water as thin as 1e-100 are checked without relaxing their gates.

## Local metric adapter, not a silent pool conversion

`SourceRelativeStorage` derives positive areas and bed gradients directly from
those fragments, and converts height differences only after subtracting the
exact source datum. It supplies the existing local hydrostatic storage and
positive kinetic-form calculations. The exact elevation datum remains a
Fraction; the local numerical datum is zero. Subsets retain original source
IDs and choose their own exact local datum. Unrepresentable positive areas
raise an error rather than being discarded.

It deliberately rejects export through the old rounded-triangle storage API.
The current evolving pool code still expects that API and float global datums.
It has **not** been switched to the new representation. Relative face heights,
internal edges, connectivity, topology events, region subsets and datum changes
must be carried consistently before that switch. Floating metric evaluation
is still bounded by represented range; exact retained polygons do not prove
all possible thin-water evolution is representable or physically correct.

## Actual South Fork controls

Run completed with exit 0:

```powershell
python -B physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/south-fork-exact-representation-v2-20260914.json --source-representation
```

Report SHA256:
`f91820ac58d60f1fa9fda724689db808631011e2b05dcb9c03464195bb85a441`.
All 35 report source hashes were checked against the final implementation.

The original 16x16 patch has 256 cells and 255 positive-volume cells. All 4,216
checked original boundary segments match the independent source-face cuts
exactly after the same final float conversion. Exact cell coverage passes.
This particular patch contains zero positive fragments with degenerate float
projections; the synthetic controls, not this snapshot, cover that case.

Independent rational wet-polygon integrals compared with the existing local
kinetic calculations on the new metrics give maximum errors:

- Relative volume: 5.9933019e-16.
- Scaled kinetic Gram matrix: 1.1361413e-15.
- Scaled depth moments: 3.4525053e-16.

The report's overall `accepted` remains false. Dry cell 158 still has no
qualified evolving closure. These tests do not advance the river or prove
the full rational model, energy conservation, breaking or froth.

## Committed front timing and the separate drying failure

The preceding commit, `242772e8e`, weights each paired dry-front force with
the same integrated donor factor as the mass transfer. This avoids applying
a full-step pressure impulse after the donor has largely drained. An
independent two-region test checks the derived velocities and momentum budget.

Its actual history report is
`tmp/south-fork-matched-front-history-v1-20260914.json`, SHA256
`d404b97c7c467ba5115c6c387b423a8d81f8c010eab1428643fb6c614235fa2b`.
It still stops at step 18 after 17 candidate steps / 0.34 seconds, with 420
regions. The earlier temporary 10.40 m/s receiver spike is removed; this is
not a qualified finite-time history. Three solved volumes become zero.
Two have no incoming net-directed transfer; the third has nonzero inflow,
so an isolated-drain deletion is not a valid treatment of all three.
Conservative drying/extinction and coupled force/topology work remain open.

## Verification and next work

Final focused tests: **195 passed, 1 failed** in 14.03 seconds, exit 1.
The unchanged failure is the old storage/face consistency gate.
`tmp/subcell-exact-representation-tests-v2-20260914.xml`.

Retained original three-file energy selection: **25 passed, 12 failed** in
7.69 seconds, exit 1. Eight nonlinear and four legacy constant-velocity
failures remain unwaived.
`tmp/subcell-exact-representation-retained-v1-20260914.xml`.

All 464 protected source, capture, map, profile and actor hashes are unchanged.
No native code, map, menu, captured terrain, runtime water state or render
quality changed. Generated reports remain ignored local files.

Next integrate the retained source representation consistently through pool
storage, relative faces and topology, then conservative drying and full
rational transport/pressure/bed work, time/open/refinement qualification and
native shared-surface integration. Actual motion and 30 FPS still require
verification; no performance gain is claimed. South Fork precedes Colorado,
Pacuare and Futaleufu; Chilko/Zambezi reviews, crew, normalization, regressions
and release checks remain open. Troublemaker remains a rapid in South Fork,
not a standalone menu scenario. Full goal remains active.
