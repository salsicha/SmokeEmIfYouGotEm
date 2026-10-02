# Eddy geometric volume and liquid support

October 1 continuation of the isolated-water-feature goal. Implemented open
volume/centroid integration and independently verified the remaining pressure
support mismatch. **Supporting geometry/phase evidence only: no new animation,
full native liquid step, changed pressure, cache, playback or game/FPS delivery.**
All eight feature acceptances remain open; existing clips are unchanged.

## New shared geometry implementation

`water_feature_extruded_volume.py` integrates the union of the unchanged seven
actual boxes and the complete actual piecewise-linear bed extrusion. It returns
open volume in m3 and first moments in m4 for arbitrary pressure-cell and
face-dual boxes. Split events come from actual roof knots and box boundaries;
roof crossings split the integration into polynomial branches. Open vertical
intervals are accumulated directly, not formed by subtracting two nearly equal
whole volumes. Overlapping solids are unioned, never counted twice. There is
no collider inflation, fitted clearance, radius adjustment or aperture cutoff.

The representation is deliberately limited to these verified laboratory
primitives. It does not replace an arbitrary curved/concave mesh with its
bounding box. Existing triangle/face construction is unchanged. This is
synthetic authored geometry, not captured river evidence or bathymetry.

Local liquid-volume bounds intersect the same actual solids with the preserved
cached trilinear liquid field. Regions split at cached-center planes so corner
extrema bound each multilinear polynomial; uncertain boxes are refined, while
actual open geometric volume weights each region. Sign guard is fixed at
1e-12 level-set units. This is a floating-point guarded bound of the supplied
reconstructed field, NOT rigorous interval arithmetic, conserved particle
mass, a measured physical interface or a complete inertia model. First moments
also do not establish connectivity of arbitrary cut regions.

## Actual preserved-state results

`geometric-inertia.json` evaluates all **117,180** original pressure cells at
frame 169, 75 mm spacing, grid 90 x 31 x 42. The eight highest absolute active
corrected face velocities are selected before liquid evaluation, not chosen
after finding convenient results. Each face's dual box and both neighboring
cells have liquid bounds at three successive refinements.

The native pressure cohort contains 11,198 cells. None has exactly zero open
geometric volume, but **1,188 pressure-cell centers lie inside actual solids**.
That is a center/support mismatch, not proof that all their open liquid is
inside rock: cut cells can have a buried center and a valid open corner.
The smallest open cell, [23,5,4], has fraction 7.51258e-13 and volume
3.16937e-16 m3. Independent liquid bounds retain that small reconstructed wet
sliver; it is not discarded with a small-volume threshold.

The sum of per-cell geometric volumes matches a separate whole-domain union
integration within 1.24345e-13 m3; first-moment error is 6.97042e-12 m4.
Whole geometric open volume is 27.26025 m3, including air and open portions
of the computational cage. It is NOT flume liquid volume or conserved mass.
The geometry-volume sum over cells flagged fluid is likewise only a cohort
measure, not a replacement for liquid integration or a particle budget.
Construction takes 14.24 seconds; this is offline geometry cost, not game FPS.

## Why the remaining fast-face result cannot be accepted

At lower face [81,26,4,0], the prior pressure reference gives 15.2709 m/s and
ghost-interface response 10.9422. Its actual open dual is only 8.33335% of a
full cell, centered at [5.7,0.79375,0.0187500] m. Both original pressure samples
lie inside the authored far wall. In the upper cell, the buried center has
cached phi +0.0432739 and is flagged empty, whereas phi at the open-volume
centroid is -0.273599. Refined bounds place essentially **100% of this open
dual in reconstructed liquid**; the neighboring open cells are wet too.
Thus the center-derived free-surface response is not the interface of the
actual open reconstructed region. This independently identifies a specific
support error, rather than accepting the speed because flux is small.

| Selected face | Prior corrected speed | Refined liquid fraction of its geometric open dual |
|---|---:|---:|
| [81,26,4,0] | 15.2709 m/s | Essentially 100% |
| [79,26,4,0] | -15.1690 m/s | 99.999994% to 100% |
| [84,26,5,2] | -13.0541 m/s | 74.7070% to 89.4531% |
| [82,4,9,2] | 9.43476 m/s | 0% |
| [84,4,9,2] | 7.58711 m/s | 0% |

The two zero-liquid duals are still given active pressure response by the
old center classification. Their lower pressure cells have partial wet
regions, so simply deleting those cells or their water is not a repair.
The other retained face results and uncertainty widths are in the receipts.
The bounds concern the original cached reconstruction only; they do not
qualify its physical accuracy or establish real interface motion.

## Independent qualification and regression coverage

`qualified.json` uses a separate Gaussian-column/vertical-partition union
integrator and explicit cached-center interpolation. It imports neither the
volume/centroid implementation nor its liquid-bound helpers. All 117,180 cell
volumes and first moments are checked against actual source geometry. Maximum
differences are 2.71051e-19 m3 and 8.67362e-19 m4. All **72** selected-region
liquid bounds are independently recomputed, along with centroid field values
and the minimum positive cell's reconstructed-liquid bounds.

All **196** numerical regressions pass. Fifteen new tests cover exact box
union/full/tangent/tiny openings, sloped roof clipping/moments, partition
additivity, dual geometry, liquid-plane and nonlinear multilinear bounds,
sloped-solid/liquid intersection, uncertain zero fields and rejected inputs.
Four new scripts compile strictly with SyntaxWarning treated as an error.
No external implementation or captured dataset is copied.

Two small receipts are copied here with SHA256 source/destination equality.
Large arrays remain at pinned C: artifact paths; they are not duplicated into
the repository. `complete=true` means the audit/qualification completed;
`accepted=false` remains explicit. Source mesh/cache fields and all old
pressure candidates remain unchanged; particles do not advance and surfaces
are not modified. Native engines are not launched for this read-only audit.
Final verification rehashes 102 unique pinned inputs/outputs across these and
the preceding pressure receipts with no conflicts or changes. The old animation
and both playback blends also reverify unchanged. Scoped whitespace checks
pass; no Blender/UnrealEditor job remains live. No Git or automation mutation
and no evidence deletion occurs.

## Next coupled implementation

Construct liquid-open face areas and dual support from the same solid/liquid
representation across the full active stencil, not buried-center flag/phi
samples. Preserve partial wet cells and uncertainty rather than relabeling
from one centroid or discarding thin water. Build the matching pressure/inertia
response together with conservative source/outflow handling and transport.
Then validate contact, liquid reconstruction, budgets and temporal/spatial
convergence before a new bake/animation. Do not merely replace the two largest
ghost coefficients, fit source flux, cap velocities or cosmetically clip
rendered water. Real circulation/foam/froth and later playable 20 FPS delivery
remain required. Keep the full isolated-feature goal active.
