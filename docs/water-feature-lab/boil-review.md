# Submerged-piston upwelling laboratory

`build_water_feature_boil.py` prepares a new 3 x 3 m closed pool with initially
still water at z=0.60 m. A radius-0.35 m cylinder has its top initially at
z=0.10 m and rises 0.24 m between frames 25 and 37, following a sampled cosine
stroke over 0.5 seconds. It remains submerged. Its bottom stays below the floor
throughout, so there is no opened under-piston water cavity. Initial liquid is
Boolean-excluded from the solid. All water-surface motion must come from the
liquid simulation, not water-mesh keyframes.

There is no continuous source or sink. The geometrically displaced volume is
0.09236 m³; liquid volume should remain conserved while the level and shape
change. This is a synthetic transient upwelling experiment, not an assertion
that an unconfined moving cylinder reproduces a natural turbulent river boil
or a piston-in-tube vortex-ring experiment.

Primary research context: [vortex-ring/free-surface interaction experiments](https://authors.library.caltech.edu/records/mvmxf-c5g95)
and [piston-generated vortex-ring experiments](https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/interaction-of-a-vortex-ring-with-a-piston-vortex/3D62422F2BA57852FC3B7B3D54CF0763).
These motivate further comparisons, not quantitative validation of this setup.
No external images, meshes, footage or paper text are bundled.

The 3 x 3 x 2.9 m, 80-resolution free-fall calibration passed: gravity error
2.02%, fit residual 0.990 mm, grid/particle peak discrepancy 1.591%. Readback
scale is 7.5977, different from the long flume; never reuse the flume's scale.
The 144-frame prepared-scene bake finished in 693.79 seconds; session 89671
is terminal. All three cache types are present. Do not launch a duplicate.

`audit_water_feature_boil.py` checks actual piston position, core vertical
velocity, annular radial velocity, radial surface elevations, reconstructed
volume and deep particle intrusion. Its particle bands are predeclared, not
selected after seeing favorable signs. Required visual checks include a local
evolving dome, radial spreading, no piston penetration or artificial waterfall,
separation from wall-reflected waves, and plausible phase/scale cues. Grid/time
convergence, mass conservation and surface transport remain unaccepted.

## First pulse measurements and preview

The completed frames 24, 28, 31, 34 and 37 have been audited while the later
cache continues baking. The initially still core velocity is effectively zero;
it rises to 0.161 m/s at frame 31, then becomes downward (-0.096 m/s) after
the stroke ends at frame 37. The fixed near-surface annulus mean radial speed
rises to +0.069 m/s, with all sampled annular particles moving outward at
frames 28..37. No particles were found more than 20 mm inside the piston.

The reconstructed central surface rises from z=0.6182 m before the stroke
to 0.6427 m at frame 34 (about 24.5 mm). The actual mesh baseline is above
the authored 0.60 m fill; this reconstruction offset must not be silently
treated as exact depth. Reconstructed volume changes from 5.2415 to 5.2166 m³
across these samples (~0.48%); this is not a solver-level conservation proof.

The first three previews (24, 37, 43) have zero foam, spray and bubble particles:
the simulation is not whitened just because it moves. The default diffuse
studio lighting barely reveals the small deformation. A separate physical
strip-light reflection improves slope visibility without changing geometry,
normals, time or cached particles. It also exposes millimetre-scale mesh noise;
optical/shape accuracy is still unaccepted. The renderer records this lighting
mode explicitly. The visible cylinder remains submerged; its rise is not the
water-surface rise.

A 36-frame clip (frames 18..53, every frame, normal-speed 24 fps / 1.5 seconds)
is delivered in `docs/water-feature-lab/boil-upwelling-prototype-v1/feature.mp4`
and `feature.png`. This shows the pulse and its early spreading, not a settled
natural boil or a seamless simulation loop. All APNG frames match their sources
exactly; MP4 decoding returns all 36 frames with no adjacent source duplicates.
First, pulse, spreading and last frames were visually inspected. Render session
75854 and encoder 97772 are terminal. No real-time performance is implied.
MP4 SHA256: `aa72bf69eba648716ebb59c4798799b603efbbb990e01a502c92eb46a18e923d`.

The executed scene checks in `test_water_feature_boil.py` passed: sampled
stroke positions, closed domain boundaries, no continuous inflow/outflow,
initial exclusion of the piston, and absence of animation on the liquid.
These are setup invariants, not acceptance of the resulting water feature.

## Late-time audit

`late-audit.json` covers frames 43, 49, 61, 85, 120 and 144. The positive
annular radial mean is still 0.062 m/s at frame 43, drops to 0.010 m/s at 49,
and becomes negative at 61 and 85. By the end, core vertical speed is near
zero. This is a decaying pulse with later return/reflection effects, not a
sustained turbulent natural boil. No deep piston intrusions were found in
these samples. Reconstructed volume reaches 5.2128 m³ at frame 144, about
0.55% below the pre-pulse value; mesh-volume stability alone is not full
mass-conservation validation. Audit session 8273 is terminal.
