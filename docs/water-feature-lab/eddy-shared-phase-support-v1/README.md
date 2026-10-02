# Eddy shared solid/liquid support across the full stencil

October 1 continuation of the isolated-water-feature goal. New all-stencil
geometric/phase fields and saved-velocity flux audit are implemented and
independently qualified. **Supporting implementation/evidence only: no new
physical step, changed pressure/cache/playback, animation, accepted feature
or playable game/FPS delivery.** Prior scenes, captures and data are preserved.

## Implemented fields

`water_feature_phase_faces.py` integrates directly the open interval union of
the original actual boxes and complete sloped-bed extrusion on physical faces.
Unlike subtracting nearly equal full/blocked areas, joint full coverage returns
zero without a small-aperture cutoff. Actual openings remain open. The seven
boxes and roof come from unchanged, fingerprinted source geometry; arbitrary
curved meshes are not replaced by boxes. Sixty previously positive represented
areas become zero in this direct-union output. Maximum difference from the
previous certified triangle areas is 2.68882e-17 m2; old arrays are unchanged.

`build_water_feature_shared_phase_support.py` produces guarded lower/upper
liquid-area and volume fields, using the SAME solid union and cached liquid
field throughout. Field signs are evaluated across the actual open regions,
not selected from a buried cell center or one centroid. Cached-center planes
split each region before multilinear extrema/refinement. Uncertainty stays
explicit at depths 1 and 2; sign guard is fixed at 1e-12 level-set units.
These floating-point bounds describe the supplied cached reconstruction, not
rigorous interval arithmetic, measured physical liquid or conserved mass.

Coverage is all **117,180 pressure cells**, all **359,412 physical faces**
including N+1 outer planes, and every **34,919 possibly-wet face dual**.
Dual boxes at the domain boundary are clipped to its actual half-volume, not
extended with invented fluid. Dual fields are evaluated only for faces whose
liquid-area upper bound is positive; omitted proved-dry-face duals are explicitly
marked. Their zero storage must NOT be interpreted as zero geometric volume
everywhere in the dual or as proof the whole dual is dry.

The 90 x 31 x 42 grid, 75 mm spacing, source solids and frame-169 checkpoint
remain unchanged. Geometry is synthetic laboratory authoring, not captured
river data or bathymetry. Construction takes 391.48 seconds and writes about
32.5 MB at pinned C: artifact paths. Those arrays are not duplicated into the
repository. This preprocessing cost is not a time-step cost or game FPS.

## Support/classification findings

At the second refinement, **12,398 cells are definitely wet**, **12,625 possibly
wet**, and **227 have unresolved wet support**. Of the cells marked empty by
the old native center classification, **1,201 have positive lower liquid-volume
bounds** in their actual open regions. No old fluid cell is proved dry. These
are common-representation findings, not permission to delete/relabel water
or to assert the cached interface itself is physically accurate.

| Axis | Possibly-wet faces/duals | Definitely-wet faces | Definitely-wet faces without positive lower dual support |
|---|---:|---:|---:|
| X | 12,156 | 11,972 | 0 |
| Y | 11,918 | 11,728 | 0 |
| Z | 10,845 | 10,773 | 0 |

There is also no possibly-wet face with a proved-dry evaluated dual. This is
a support consistency check, not a validated kinetic mass matrix or pressure
boundary condition. Previously retained fast faces remain in the receipts;
the 15.2709 m/s floor/wall face is nearly fully wet, while the 9.43476 and
7.58711 m/s top faces are proved dry in the supplied reconstruction. Their
saved velocities are not capped or overwritten.

Total reconstructed-liquid bounds narrow from [3.855518,4.108395] m3 to
[3.918710,4.044877] m3. The remaining 0.126167 m3 uncertainty is material.
This is fixed-checkpoint quadrature refinement, NOT spatial CFD convergence,
a change in liquid mass, an emission/removal budget or accepted conservation.

## Common-field Cartesian flux intervals

`water_feature_phase_flux.py` uses the same stored physical face for both
neighboring cells, carrying area uncertainty and velocity sign into conservative
Cartesian flux intervals in m3/s. Missing N+1 native boundary velocities are
not invented: evaluation is allowed only because those upper boundary liquid
areas are independently proved zero. A nonzero possible area would fail.

`cartesian-flux.json` evaluates the unchanged before-pressure, native public
projection and old consistent-reference velocities on these SAME phase fields
and cohorts. At a fixed diagnostic allowance of 1e-8 m3/s, the definitely-wet
cohort has 10,765 / 2,194 / 1,257 cells whose Cartesian flux intervals exclude
zero, respectively. The old-reference maximum distance from zero is
0.0230665 m3/s at [82,4,4], interval [-0.0232198,-0.0230665] m3/s. Within the
1,201 previously-empty but definitely-wet cells, that old reference has 666
zero-excluding intervals. The previous narrow-cohort small geometric flux
residual is therefore not proof of a complete shared liquid update.

These numbers are **NOT full liquid incompressibility residuals or mass drift**:
internal moving-free-surface flux, actual time evolution and emission/removal
are absent. Cartesian liquid-volume flux can be nonzero in a moving cut cell.
All-domain Cartesian boundary flux is zero; that is only a shared-face/boundary
ledger, not conserved physical mass. Summing per-cell interval endpoints would
discard shared-face correlation and is deliberately not used as the domain
flux. Do not fit source flux or pressure to force these diagnostic intervals
to zero without the missing physical terms.

## Independent verification and preservation

`qualified.json` imports no construction helpers; its reference helpers are
separate implementations predating this phase-field construction.
It uses independently interpolated half-cell nodes, analytic vertical-column
geometry, separate cached-field interpolation and Gaussian volume integration.
At BOTH depths it checks every stored cell bound and physical face bound, plus
every declared possibly-wet dual bound: 234,360 cell-bound pairs, 718,824
face-bound pairs and 69,838 dual-bound pairs. Maximum errors are 1.76183e-19
m3 (cells), 2.71051e-19 m3 (duals), 8.67368e-19 m2 (liquid areas) and
1.14455e-18 m2 (geometric areas). Independent geometry subtraction retains
roundoff; these tolerances are not general continuum accuracy guarantees.
Full verification takes 1,430.82 seconds; it is offline diagnostic cost.

All **212 numerical regressions pass**, including 11 new phase-face/coverage
tests and 5 Cartesian-flux tests. Seven new scripts compile with SyntaxWarning
as an error. A separate readback check independently verifies 75,072 cohort
cell evaluations across all three saved velocity stages without importing the
flux constructor. Tests cover tiny openings, joint box/roof coverage, nonlinear
phase bounds, false center interfaces, half-cell/N+1 coverage, equal/opposite
face flux, negative velocity orientation, correlation and missing-velocity
rejection. No native solver or renderer is launched in this continuation.

Three small receipts are copied here with SHA256 equality: `shared-phase.json`,
`qualified.json`, `cartesian-flux.json`. `complete=true` means construction/audit
finished; all have `accepted=false`. No old data/source/animation is changed;
no particles advance and no source flux, pressure or surface is modified.
Final verification rehashes 142 unique pinned files across these and the prior
geometry/pressure receipts, with no conflicts or changes. The previous animation
and both saved playback blends also reverify unchanged. Both new workers finish
terminal 0; no Blender/UnrealEditor job remains live. Scoped whitespace checks
pass. No Git/automation mutation or evidence deletion occurs.

## Next coupled repair

Resolve/refine uncertainty where needed and derive the pressure gradient,
divergence, kinetic inertia and free-surface conditions together on this shared
representation. Internal free boundaries and source/outflow chronology must be
included; areas and dual volumes must not be blindly interchanged as weights.
The authors' [variational coupling notes](https://www.cs.ubc.ca/labs/imager/tr/2007/Batty_VariationalFluids/)
explicitly distinguish face-area from volume weighting and discuss associated
free-surface conditions. This is a method reference, not copied implementation
or proof that the present fields instantiate that complete method.

Then perform matched physical-step/energy/contact/transport/budget tests and
refinement before baking another animation. Do not promote midpoint measures,
old center flags, a few changed ghost coefficients, cosmetically clipped water
or source fitting as the full repair. Accurate animations of all eight features
and later normal playable river integration at 20 FPS remain required. Keep
the complete isolated-feature goal active.
