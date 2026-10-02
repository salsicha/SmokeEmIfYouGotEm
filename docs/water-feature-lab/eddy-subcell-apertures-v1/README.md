# Eddy subcell geometry: verified areas, still incomplete pressure coupling

October 1 continuation of the user's isolated-water-feature goal. **Supporting
implementation/physics evidence only: no new animation, accepted feature,
changed native playback/cache, full CFD bake or playable game/FPS delivery.**
The explicit-wall animation and both saved playback scenes remain unchanged.
The new pressure experiment rejects simply replacing native fractions while
retaining cached flags. Do not start a full bake of that control.

## Implemented boundary geometry

`water_feature_subcell_geometry.py` now constructs solid/plane intersections
from the actual closed collider triangles, then clips and unions their polygons
on every physical Cartesian face. Shared source-edge identifiers retain closed
sections without epsilon welding or moving vertices. Ring parity handles holes;
overlapping solids are unioned, not double-counted. Coplanar surface patches
block their faces. Open meshes, degenerate source triangles and unresolved
branching sections fail rather than being filled. This closure check does not
certify arbitrary self-intersecting solids; the tested laboratory meshes are
the preserved seven boxes and one rectangular piecewise-linear bed extrusion.

All eight original collider world-vertex/triangle hashes match the existing
control. Original dimensions, cutaway-wall disclosure, source/floor/slope/spur,
75 mm spacing, 90 x 31 x 42 grid and origin are retained. Synthetic laboratory
geometry is not measured river evidence or inferred underwater bathymetry.

`actual-inputs.json` exports seven preserved frame-169 cache fields and all
colliders without changing RNA domain settings, source files or cache contents.
`geometric-apertures.json` records all **359,412 faces**, including the N+1
outer planes on each axis, and per-plane intersection proofs. Full face areas
are in m². Native shortened MAC storage receives the lower N faces divided by
h²; outer faces remain preserved, not guessed from half-cell SDF extrapolation.

The polygon algorithm integrates linear union intervals between all endpoint
and edge-crossing events. Adjacent float64 events need not have a representable
midpoint; edge selection therefore uses the entire interval rather than a
rounded midpoint. Physical h² area is normalized by the same floating-point
world rectangle used for clipping, eliminating negative roundoff-only areas.
There is no fitted wall clearance, inflation, SDF interpolation, raster
occupancy, convex-hull fill or imposed fluid state. Tiny positive areas are
retained; conditioning of near-closed cut cells is not yet qualified.

## Independent geometry qualification

`qualified.json` checks every face with a separate interval-envelope reference
that does **not** import the section/clipping/union implementation. It verifies
actual box vertices and all boundary triangles of the complete 121-column bed
extrusion, then integrates its actual piecewise-linear roof and box intervals.
Maximum per-axis area differences are 1.87e-18, 3.04e-18 and 1.87e-18 m², below
the predeclared 2e-12 m² roundoff allowance. This is finite-geometry agreement,
not continuum physical accuracy, grid convergence or cell-volume conservation.
The reference's tiny negative fully-blocked values are subtraction roundoff,
not negative areas supplied to the native solver. Supplied areas are finite
and within [0, h²]. Construction took 59.69 seconds; independent geometry and
pressure-readback qualification took 10.06 seconds. These CPU diagnostic costs
are not interactive FPS or acceptable production preprocessing benchmarks.

## Actual owned native pressure experiment

`native-pressure.json` uses installed Blender 5.2.0 LTS build `fbe6228777e7`,
new owned native grids and the unchanged frame-169 cached initial MAC velocity
and liquid/obstacle/inlet/outlet fields. Each pressure starts at zero (pressure
is not a cached state). Explicit cgAccuracy=1e-6 and cgMaxIterFac=6 are recorded;
this is a pressure-only experiment, **not** the installed complete liquid-step
chronology or a simulated additional frame. No particles advance, no source
emits, no surface is extracted, no elapsed time is altered and no cache is baked.

The native baseline reconstructs uncached fractions with the actual namespace
settings boundaryWidth=1 and fracThreshold=0.05, then rebuilds obstacle flags
and updates fluid flags from the same cached liquid field. Its flags match the
original cache bit-exact. The geometric fixed-flags control uses those SAME
flags. A third control rebuilds native flags from geometric areas; this changes
6,027 total cells and the tested fluid cohort from 11,328 to 11,199 cells.
This is not evidence of a matching liquid volume or conserved particle mass.

The matching source constructs native fractions from a **center-to-center
normal line segment**, not a two-dimensional geometric open area.
[Native updateFractions](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/plugin/initplugins.cpp).
The pressure RHS consumes weighted face velocities; independently assembled
lower-face arithmetic agrees with the actual native RHS within 5.37e-7 native
units in all three controls (fixed allowance 5e-5).
[Native pressure operator](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/plugin/pressure.cpp).
No external source code is copied or bundled.

Physical velocity conversion stays u_world = u_native x h x 2.5, so weighted
divergence is in s^-1. Do not use the display-resolution divisor as the native
unit scale or report native pressure as calibrated physical pressure.

| Control | Geometrically closed cells flagged fluid | Geometric cut-cell divergence RMS before / after pressure | After-pressure maximum on cut cells |
|---|---:|---:|---:|
| Native distance-segment fractions | 168 | 1.459 / 1.478 s^-1 | 15.429 s^-1 |
| Geometric areas, same native flags | 168 | Native CG diverges; no result accepted | Not available |
| Geometric areas, rebuilt native flags | 0 | 1.448 / 0.484 s^-1 | 9.423 s^-1 |

The fixed-flags native solver raises its residual-norm >1e30 divergence error.
`closed-pressure-rows.json` independently recounts the168 closed fluid cells:
87 have no empty neighbors and therefore neither face weights nor the matching
source's empty-neighbor ghost-fluid diagonal contribution. The other81 DO
have empty neighbors; that native diagonal is unweighted by apertures, so
do not claim all168 have zero operator rows. This classification is consistent
with a singular coupling, but is not direct native matrix readback or unique
attribution of every source of divergence. The failure is preserved, not bypassed or mislabeled
as convergence. The parent pressure receipt intentionally has complete=false
because one control failed; the independent qualification has complete=true
because it checks the two finite controls and that explicit retained failure.

Even rebuilt flags leave whole-cohort geometric divergence RMS 1.438 s^-1,
maximum 16.611 s^-1. These are substantial remaining errors; neither an
incompressible repair nor pressure convergence is claimed. The row's own
before/after values share its cohort, but native-versus-rebuilt cohort values
are not a matched causal comparison because the flags differ.

The final native fractional wall treatment derives normals from the unchanged
cached obstacle field, rather than consuming geometric face areas/normals.
[Native setWallBcs](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/plugin/extforces.cpp).
It slightly changes the baseline's flux residual; the rebuilt geometric
control is unchanged by that final wall call in this one snapshot. This does
not qualify oblique wall motion or establish that the wall treatment is fixed.
Both finite controls save flags, fractions, RHS, three velocity checkpoints
and pressure. Independent qualification re-integrates geometric divergence
from those saved readbacks with a fixed float32 arithmetic allowance. No
interior-only masking is used to hide all cut-cell/interface errors.

## Preservation, failures and next implementation

Five JSON receipts are copied here with SHA256 equality. Large owned arrays
remain at their pinned C: artifact paths, not duplicated into the repository.
Input hashes and live host scalar fields are checked unchanged. Earlier
prototype attempts are preserved separately: missing midpoint parity,
roundoff-negative area normalization, native flag-constant namespace mismatch,
and RHS index-shape mismatch. The first two native adapter failures occurred
before projection; they are not hydraulic results. The v3 experiment is the
qualified pressure control. No unchanged rejected run is repeated.

All169 numerical regressions pass, including13 new polygon/subcell tests.
Seven new Python files compile strictly with SyntaxWarning as an error.
Scoped whitespace checks pass. Final verification rehashes the56 pinned
files in the independent area/pressure qualification, confirms matched native
flags and the retained failed control, and separately verifies the previous
explicit-wall animation and both playback blends unchanged. The additional
closed-row receipt pins its independent audit, reports, flags and three area
arrays. No owned Blender/UnrealEditor process remains running. No source-access
blocker, Git mutation, automation change or evidence deletion occurs.

Next identify the remaining pressure/free-surface/flag consistency error using
actual matrix and corrected-velocity residuals, then couple geometric face and
cell representation with collision trajectories and liquid reconstruction.
Do not delete primary water to match changed flags, fit a surface radius,
cosmetically clip a render mesh or promote the singular fixed-flags control.
Swept contact, liquid budgets, cell volumes/inertia, refinement, persistent
eddy circulation, foam optics and all other seven features remain open.
Later normal playable integration still requires actual motion and the user's
20 FPS goal. This turn has no visible delivered change or new river acceptance.
