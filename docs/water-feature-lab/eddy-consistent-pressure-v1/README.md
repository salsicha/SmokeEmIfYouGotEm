# Eddy pressure response: consistent operator, physical acceptance still open

October 1 continuation of the isolated-water-feature goal. Supporting geometry
and pressure implementation only: **no new animation, full liquid step, native
cache/playback change, accepted feature, playable river or FPS delivery.**
The previous explicit-wall animation and both playback files are preserved.

## Delivered implementation

`water_feature_consistent_pressure.py` implements a uniform-density Cartesian
pressure-impulse reference whose matrix and velocity correction use the same
face response. Fluid-fluid weights use the geometric aperture; fluid-air
weights also use the cached liquid-interface distance. Both orientations of
prescribed fluid-outflow velocity have zero pressure response. No fitted source
flux, compatibility-mean adjustment, pressure shift or particle deletion is
used. Unsupported fluid cells fail explicitly. A fresh matrix residual must
meet the fixed 1e-8 native-unit tolerance before float64 CG is accepted.
This is not calibrated physical pressure or a replacement CFD simulator.

The actual installed Blender 5.2.0 LTS build is `fbe6228777e7`. Owned native
`correctVelocity` grids reproduce both preserved finite native projections
bit-exact. Actual `computePressureRhs` readbacks check the new candidate velocity
in native float32 storage. There is no hidden native-matrix readback or native
solver monkeypatch. Source-host loading precedes Mantaflow imports; the original
domain RNA, geometry and cached fields remain unchanged.

The matching source's fractional matrix diagonal sums face fractions, while
off-diagonals require fluid neighbors; its liquid-air ghost diagonal is not
aperture-weighted. The velocity correction skips outflow-storage cells, but
the opposite orientation can still respond. These source structures motivate
the consistent reference; they are not direct hidden-matrix measurements.
[Matrix construction](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/conjugategrad.h),
[pressure and velocity kernels](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/plugin/pressure.cpp).
These files identify Apache-2.0 licensing. No external implementation is copied
or bundled; the reference is independently implemented face arithmetic.

## Retained counterexample and exact closure repair

The first consistent projection passes flux but produces a **303.958 m/s**
active-face jet. Its aperture fraction is 1.110223e-16, from cancellation in a
face fully buried in the unchanged floor. Small divergence therefore does not
prove credible velocities. That failed physical candidate is retained in
`pressure-response.json`, not promoted into a bake.

`water_feature_box_face_certificate.py` checks each actual eight-vertex,
twelve-triangle closed box, then proves full face containment using unchanged
world bounds. `certify_water_feature_blocked_faces.py` closes only proved faces.
Of all 359,412 physical faces, **2,220** change: 1,705 / 194 / 321 on axes
0 / 1 / 2. Each falsely open area was 6.2450045e-19 m2. All unproved and
partially open faces stay bit-exact. There is no aperture threshold, geometry
inflation, velocity cap or bounding-box approximation of the sloped bed.
The smallest positive synthetic opening remains open in the regression test.
This certificate covers the seven original boxes, not arbitrary curved solids
or faces jointly covered only by several solids.

## Actual pressure-only results

The preserved frame-169 state uses 75 mm spacing on a 90 x 31 x 42 grid.
Native velocity to m/s conversion is x0.1875; divergence to s^-1 is x2.5.
These are weighted face-flux residuals, not cut-cell-volume-normalized
divergence. Changing flags changes the cohort; cross-row differences are not
a matched conserved-liquid comparison.

| Control | Fluid cells | Whole-fluid maximum weighted divergence after pressure | Physical disposition |
|---|---:|---:|---|
| Original geometric areas, native public solver | 11,199 | 16.6105 s^-1 | Fails flux |
| Original geometric areas, consistent reference/native float32 readback | 11,199 | 3.72529e-6 s^-1 | Flux passes; 303.958 m/s jet rejected |
| Certified box closures, native public solver | 11,198 | 16.6194 s^-1 | Still fails flux |
| Certified box closures, consistent reference/native float32 readback | 11,198 | 3.72529e-6 s^-1 | Flux passes; physical velocities/contact not accepted |

The old native-distance-segment input cannot support the symmetric prescribed-
outflow reference: 16 fluid cells have no pressure-response stencil. Their
indices and rejection are retained; no liquid is removed to force a solve.
The earlier singular geometric fixed-flags control is not rerun.

The certified reference takes 140 CG iterations and 0.262 seconds in this
snapshot. Native RHS maximum is 1.49012e-6 against the predeclared 5e-5 native
allowance. Independently re-integrated native float32 flux RMS is
6.75183e-7 s^-1. All 201 open prescribed-outflow faces stay bit-exact.
These diagnostic costs are neither full-step simulation costs nor game FPS.

Closing the proved floor face removes its pressure response and the roundoff
jet without capping velocities. The remaining active peak is **15.2709 m/s**
at lower MAC face [81,26,4,0], world position
[5.7,0.825,7.15256e-8] m, aperture fraction 0.08333347.
That partial-face velocity remains physically unqualified. Tiny partial-cell
volumes/inertia, liquid geometry and transport are not solved by face apertures
and pressure projection alone.

## Independent qualification and preservation

Four small JSON receipts are copied here with source/destination SHA256 equality:
`pressure-response.json`, `certified-apertures.json`, `certified-pressure.json`
and `qualified.json`. Large owned arrays remain at pinned C: artifact paths;
they are not duplicated into the repository. Laboratory geometry is synthetic,
not captured river data or inferred bathymetry.

The qualifier imports neither pressure construction nor box certification.
It checks every face with an independent actual-box containment proof,
independently recomputes the gradient and native float32 corrected velocity
bit-exact, checks weighted divergence/native RHS and frozen outflow faces, and
retains both the unsupported-input and high-velocity counterexamples. Report,
array, source-host and implementation hashes are rechecked. `complete=true`
means evidence qualification finished; every candidate has `accepted=false`.

All **181** numerical regressions pass, including eight pressure and four
box-certificate tests; eight new scripts compile with SyntaxWarning as an
error. Early setup rejection and the partial v1 qualifier JSON from a numpy
integer serialization failure are preserved; complete v2 qualification is
the authoritative receipt. No previous source/cache/animation is overwritten,
no native primary particles advance and no liquid surface is changed.
Final verification rehashes 94 unique pinned inputs/outputs, plus the previous
animation and both playback blends, with no changes or conflicting versions.
No Blender or UnrealEditor process remains running. Scoped whitespace checks
pass. No Git mutation, automation change or evidence deletion occurs.

## Next implementation gates

Extend exact full-coverage predicates beyond single boxes; couple partial-cell
volumes/inertia, liquid interfaces and active-face support with the same solid
geometry. Then validate swept contact, native chronology/source conservation,
surface reconstruction, trajectories and spatial/temporal refinement before
baking another animation. The 15.2709 m/s partial-face result and prior slope/
spur contact failures must not be hidden with clearance/radius fitting,
particle removal, flux fitting or cosmetic render clipping.
All eight feature acceptances and later normal playable integration at the
user's 20 FPS goal remain open. The isolated-feature goal stays active.
