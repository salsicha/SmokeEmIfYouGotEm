# Internal source-region faces and conditioning

September 14, 2026. **Internal coupling verified; activation and gameplay remain open.**

The preceding actual-state audit found unowned receiving source support in 18
cells, including 17 cells with existing water elsewhere. New water on that
support cannot safely be assigned to an unrelated pool or merged immediately
into a single parent-cell level. Independent source regions need real internal
mass and pressure faces, including oblique original mesh edges.

## Implementation

`subcell_source_region_faces.py` builds those internal faces from original mesh
vertex/triangle IDs. Edge clipping and side predicates use exact rationals of
the represented source coordinates. Point contacts and vertical projected edges
are not connections; edges lying on the Cartesian box belong to the existing
box-face path. Hydraulic length is the horizontal projected edge length. The
outward normal comes from the original source triangle, not a rounded-coordinate
match or a cell-center direction.

`WetPoolPartition.with_regions` accepts explicit independent region states. It
checks positive volumes, finite momenta, disjoint original source ownership and
connected wet support. It does **not** claim to preserve a supplied old state's
mass, momentum or energy: those transition budgets remain the caller's job.
No force-merging or dry-volume seeding occurs in this API.

New region topology checks retain the water height as a local offset plus datum.
Tests keep volumes down to 1e-150 positive even when adding that offset to the
absolute datum rounds back to the dry bed elevation. Subsequent volume probes
check the paired local height against actual source vertex levels. No wet-depth
floor or small-pool deletion is introduced.

The exact pressure matrix, its changing-volume direction and its reverse energy
gradient all include the same internal edges and normals. Both original poles
and both physical momentum components are retained. The nondispersive base flux
uses an orthonormal normal/tangent transformation of the existing face flux;
global XY momentum is transformed back. Its internal faces contribute to the
independent hydrostatic boundary/bed-force closure.

Wet internal edges facing unowned support are reported as activation requests.
They are not silently omitted or converted into walls. Incomplete transport
continues to return null rates. Dry rock ridges remain uncoupled.

## Actual conditioning failure and correction

The controlled actual-source probe subdivides fully wet parent cell 112 into
its 16 original source-face regions, holding its initial level and velocity
unchanged. Across the full patch this changes 258 unknowns to 273, with 19 new
common-wet internal pressure edges, including seven oblique edges. Measured
parent volume and momentum differences in this run are both zero.

The first complete report, `tmp/south-fork-internal-regions-v2-20260914.json`,
failed the strict physical momentum round-trip gate: 5.0522409721598116e-5 error
after dividing each pool's momentum error by its volume. Small component tests
had not exposed this conditioning problem. Its report remains a failed result.

The correction preconditions each connected same-parent source-region group's
**exact principal pressure block**. Groups form only through actual common-wet
internal edges; dry-separated pools are not grouped. Local matrices include all
of the original factor contributions, including those from neighboring rows.
Their Cholesky factors are used only as a symmetric positive preconditioner.

The physical operator, poles, 40-CG budget and all residual/round-trip thresholds
are unchanged. This is not a pressure solve reset, changed RHS or finer-grid
waiver. The original 258-pool snapshot has no common-wet internal groups and
retains its previous 2x2 preconditioner path and static pressure results.

Tests compare the source blocks against independently assembled principal
matrices, check positive symmetric preconditioning, and retain exact equality
of the two preconditioning paths when no internal source group exists.

## Final actual-source evidence

Report: `tmp/south-fork-internal-regions-v3-20260914.json`.

SHA256: `67f79d80c8558fedb4b8f0ea24a18868a25600c7dde6216c761dcfb4282dbe30`.

| Controlled 273-region check | Result |
| --- | --- |
| Physical momentum round-trip error per pool volume | 1.6569440868903862e-10 |
| Canonical velocity vs dense original response inverse, maximum pool-scaled error | 1.3877787807814457e-14 |
| Reverse vs independent forward volume-work error | 1.856681302315064e-15 |
| Original pole true residuals | 5.5513e-13 and 2.7408e-16 |
| Positive inverse-factor true residuals | 3.6266e-16 and 2.0889e-16 |
| Iteration budget | 40, unchanged |
| Largest scaled energy directional-probe discrepancy | 1.2897e-8 |

Internal-region and physical-energy component controls pass. The original
snapshot still has the same 66 raw unowned receiving trace entries across the
same 18 cells; the subdivided snapshot also reports 66. The overall audit
**exits 1** because complete actual transport remains unsupported. No unavailable
rate or diagnostic pass is counted as a wetting solution.

Subdivision is not an energy-neutral physical transition: model kinetic energy
changes from 2156.913766390772 to 2163.373205191622, an increase of
6.459438800850421 in the model's energy units. Potential energy changes only at
roundoff. Holding represented volume, momentum, water level and velocity fixed
does not guarantee equality of the coarse and subdivided discrete pressure
metrics. This is a measured remapping issue, **not physical energy creation
accepted by the solver**, breaking dissipation or a reason to adjust a gate.

## Tests, preservation and next work

Final exact-subcell/triangle suite: **133 passed** in 12.13 seconds, including 11
new internal-region tests. Report:
`tmp/subcell-internal-regions-tests-v3-20260914.xml`.

Retained original stress/constant-velocity suite: **34 passed, 12 failed** in
9.09 seconds, exit 1. Eight paired-base nonlinear energy failures and four legacy
constant-velocity failures remain unwaived. Report:
`tmp/subcell-internal-regions-retained-gates-v2-20260914.xml`.

All 464 protected source/capture/map/profile/actor hashes were rechecked and are
unchanged. Original mixed source authority is retained; inferred submerged
terrain and connecting flanks are not promoted to measured bathymetry.

Next implement source-supported one-sided activation with explicit incoming
mass/momentum and energy budgets. New regions can now communicate across their
real internal edges, so activation need not force disconnected water to a
common level. Handle topology/remapping energy and later coarsening explicitly;
the controlled subdivision above is not itself an accepted transition. Complete
rational auxiliary transport and bed-force work, then wet-front/finite-time/
open/refinement/native/shared-surface qualification.

No ordinary native solver, water state, scenario, rendered surface or quality
setting changed. South Fork's visual and 30 FPS gates remain failed. Colorado,
Pacuare, Futaleufu, all-scene Chilko/Zambezi reviews, crew realism/fit/animation,
normalization, outstanding regressions and release work remain open. Troublemaker
is a rapid inside South Fork, not a standalone menu scenario. Full goal active.
