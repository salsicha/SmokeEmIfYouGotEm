# Eddy corner mechanism: closest-node replacement is not a repair

October 1 continuation of the isolated-feature goal. Supporting native physics
diagnostics only: **no new animation, accepted feature, changed Blender playback,
full CFD bake, playable game update or FPS claim**. The previously delivered
two-second explicit-wall animation and both standalone playback scenes remain
unchanged in `../eddy-explicit-walls-v1/`.

## Outcome

The actual cached obstacle field does not reproduce sharp authored corners.
Replacing its nodes with closest-distance samples from the same eight closed
colliders changes native pressure/velocity, but does not repair contact. All
twelve matched native-step controls fail sampled authored contact. Do not
promote this replacement into the existing scene or start a full bake of it.
The next treatment needs shared subcell geometry for pressure, collision and
surface reconstruction, not just improved distances at coarse grid nodes.

All geometry remains the original synthetic laboratory geometry. No rock is
hidden, moved, rounded, inflated or removed to make this diagnostic pass.
There is no particle deletion by the audit, contact projection, radius tuning,
cosmetic clipping or replacement of a native cache. Native particle adjustment
during the measured step is retained as an actual solver operation.

## Evidence and scope

`standard-contact.json` and `fractional-contact.json` inspect actual preserved
frames 145, 169 and 191. Every primary record independently matches Blender's
displayed coordinates after typed native VDB loading. All flags are retained.
All original field-derived vertices and triangle centers are tested against
all eight closed physical collider meshes, including the disclosed cutaway
walls. Deepest twelve contact locations per cohort/solid are retained with
nearest authored surface, eight neighboring cached field values, flags and
closed-BVH distance/parity at those same eight world positions.

These are complete counts for the tested cohorts, but deepest-point diagnostics
are not whole trajectories, exhaustive triangle intersections or finite-sphere
clearance. BVH parity uses the existing 1 micrometre contact tolerance. Float32
mesh precision does not establish micrometre continuum physical accuracy.

For example, a spur-contact vertex at (2.475, 0.06984644, 0.15000007) m is
19.846 mm inside the authored spur while cached obstacle interpolation is
approximately zero. One neighboring point at (2.4375, 0, 0.15000007) m has
cached positive distance 119.385 mm versus closest authored distance 51.539 mm.
At the approach hinge, the vertex (0.6, 0.75, 0.43873050) m is 10.080 mm inside
the authored bed while cached obstacle interpolation is approximately zero.
The largest distance discrepancy among the retained eight-node stencils is
87.500 mm; this includes interior/overlap nodes and is NOT a whole-grid surface
offset. Cached `phi_obstacle_inflow` at these locations is already processed;
the diagnosis does not isolate every error to raw host voxelization alone.

The installed compiled step is disassembled in both contact receipts. It uses
the obstacle level set for native primary contact, pressure boundary treatment
and exclusion. The source matching installed Blender build `fbe6228777e7`
shows volumetric mesh distances estimated with 26 ray directions; it does not
perform a closest-triangle Euclidean query in that volumetric branch.
[Blender fluid.cc, update_distances](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/source/blender/blenkernel/intern/fluid.cc).
The matching particle contact kernel samples that field and applies one
normalized-gradient displacement when the sampled distance is negative.
[Native FLIP contact kernel](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/plugin/flip.cpp).
These are source explanations alongside actual installed-kernel measurements,
not proof that one source edit or gradient iteration would repair the full flow.

## Matched coupled-input experiment

`standard-evolution.json` and `fractional-evolution.json` run three independent
late-state pairs on newly owned native grids/primary particles. Each pair starts
from identical cached state and runs the **exact installed compiled liquid-step
code**, not a rewritten solver or a monkeypatched native class. Both controls
receive the SAME native obstacle-flag preparation. Fractional controls both
reconstruct uncached native face fractions before pressure; zero fractions
must not be mistaken for a restored fractional state.

Baseline final/input obstacle fields are loaded separately and kept distinct.
The changed control supplies closest closed-mesh signed-distance nodes to both
fields, native face fractions/obstacle flags, pressure and primary contact.
That field is the signed minimum over eight solids; it has the correct union
sign/zero set at queried nodes but is not the exact Euclidean distance of an
overlapping-solid union. Cell spacing stays 75 mm, shape 90 x 31 x 42, original
origin and geometry unchanged. There is no fitted surface clearance.

Each control advances ONE native substep of 0.02083333284 physical seconds from
frames 145/169/191. No host emission, dynamic-solid reconstruction, complete
adaptive-frame chronology or secondary-particle evolution is replayed. These
are independent local pressure/contact experiments, not simulated additional
full frames, a valid replacement cache or a settled eight-second repaired flow.
Uncached stationary force and solid velocity are verified zero, not invented.

All loaded cached grids are checked bit-exact against independent OpenVDB;
primary positions/velocities match native display. Exact-code hashes match
within each pair. Post-step phi, obstacle, velocity and pressure arrays are
saved and finite. A fresh native 2x extraction of each post-step field is
measured unchanged; this extraction refinement is NOT CFD grid refinement.

| Maximum across the three local steps per mode | Cached geometry | Closest-node geometry |
|---|---:|---:|
| Standard primary spur intrusion | 14.073 mm | 14.073 mm |
| Fractional primary spur intrusion | 30.304 mm | 30.305 mm |
| Standard primary approach intrusion | 10.930 mm | 10.614 mm |
| Fractional primary approach intrusion | 10.652 mm | 10.317 mm |
| Derived spur intrusion, either mode | 20.833 mm | 19.519 mm |
| Derived approach intrusion, either mode | 10.080 mm | 9.634 mm |
| Derived far-wall intrusion | 0 mm | 12.501 mm |
| Derived floor intrusion | 0 mm | 0.002328 mm |

All twelve sampled primary-plus-surface contact gates fail. The changed field
also increases the count of shallow approach contacts in these trials. Its
small reduction of worst approach depth is not overall contact acceptance.
Pressure/velocity arrays change, so this was a coupled-input test, not a
render-only edit. Reported maximum deltas are native full-domain scalars,
not calibrated physical pressure, fluid-only error, discharge or stability.

## Independent qualification

`qualified.json` independently rehashes 108 pinned inputs/outputs, verifies both
closest-node fields bit-exact between solver modes and every changed post-step
obstacle array bit-exact with its supplied field. Every retained contact stencil
is checked against the saved baseline field and the closest-node geometry;
the declared 4 micrometre float32/BVH node allowance is not a physical contact
allowance or a fitted tolerance. All paired initial states, clocks, native-code
bindings and geometry-preparation protocol agree.

All twelve post-step volume estimates are independently reintegrated at 8 and
16 subdivisions. The 8-subdivision values reproduce the native experiment
reports within float64 summation allowance. Quadrature changes reach 0.020090
m3 in standard and 0.023045 m3 in fractional mode, larger than some paired
volume differences. Do not claim conserved mass, a volume improvement or
convergence from these interface-volume estimates. Geometry-only volume changes
occur before evolution; this is another reason not to equate unchanged authored
solids with unchanged effective solver fluid volume.

The 156 existing numerical tests pass; four new diagnostic/qualification scripts
compile strictly with SyntaxWarning treated as an error. Tests are supporting
evidence, not feature acceptance. Native jobs are terminal. No old file, source
cache, scene, clip, receipt, game build, Git ref/history or automation is changed.
New JSON reports are copied with source/destination SHA256 equality; large
owned arrays and OBJ diagnostics stay in their original C: artifact directories.

Final cross-delivery verification rehashed 6,402 unique pinned files across
49 JSON reports (five new, forty-four preserved) with zero conflicts or changed
files. The delivered explicit-wall APNG and both standalone playback blends
were separately verified unchanged. All four new source scripts compile
strictly; the scoped Git whitespace check passes. No Blender/UnrealEditor
process remains running after the owned tests finish.

Two early standard adapter failures (inactive fractional grid was None; an
uncached pre-step input grid was not allocated) and one early fractional trial
with unconstructed fractions/nonfinite readback are preserved, not accepted.
The first completed standard experiment also used asymmetric geometry-flag
preparation and is superseded for causal comparison. This folder contains only
the corrected matched-protocol experiments and their qualification. Do not
rerun those failed/incomplete trials unchanged or confuse them with failed
original 192-frame bakes. The original controls continue to load normally.

## Next implementation target

Prototype a corner-preserving subcell representation on owned resources: retain
actual collider intersections/face apertures and normals, use the same geometry
in pressure boundary constraints, trajectory contact and surface reconstruction,
and assess swept collision, discrete flux/volume budgets and refinement. Closest
node fields alone are now experimentally rejected. Preserve source dimensions,
physical time, native unit conversion and all old evidence. Do not repair only
the render surface or compensate lost liquid with a radius/volume fit.

The variational fluid/solid coupling work provides a primary reference for a
geometry-aware pressure treatment, not an already implemented or validated
solution here: [Batty, Bertails and Bridson (2007), author publication page](https://www.cs.ubc.ca/labs/imager/tr/2007/Batty_VariationalFluids/).
Only source/publication references are recorded; no external code, PDF, footage
or licensed imagery is bundled. All laboratory geometry remains synthetic,
not measured river evidence or inferred underwater survey geometry.

The full user goal remains active: all eight isolated feature environments and
physically/visually accurate short animations, then realistic playable river
integration. No water feature is accepted by this diagnostic delivery.
