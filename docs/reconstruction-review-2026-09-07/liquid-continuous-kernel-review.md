# Continuous sparse surface reconstruction — September 9, 2026

Isolated South Fork candidate, not production promotion or photorealistic
acceptance. Follows the [optical comparison](liquid-river-optics-review.md).

## Investigated and changed

The inherited reconstruction switches an entire particle kernel between a
sphere and an anisotropic ellipsoid at **25 neighbors**. This threshold follows
the example in [Yu and Turk, equations 14–16](https://faculty.cc.gatech.edu/~turk/my_papers/sph_surfaces.pdf).
It is discontinuous when one neighbor barely crosses the support radius, even
though that neighbor has almost zero covariance weight.

An opt-in `-RaftSimLiquidSmoothSparse` candidate replaces the count switch with
a smoothstep in weighted neighborhood support: subtract self weight, then blend
between 8 and 24 weighted neighbors. These limits are an authored extension,
not values established by that paper or measured river data. Sparse isolated
particles remain spherical, dense neighborhoods retain the existing anisotropic
fit, and degenerate covariance remains finite. Existing radius, voxel prefilter,
quadrature weights, primary positions, solver geometry and flow are unchanged.
The GPU remains fully live; the flag defaults off for controls and other callers.

The synthetic threshold test moves one neighbor by two micrometers across the
0.8 m support boundary. The old unfiltered axis changes by over 5 cm; the new
axis change is below 0.001 cm. A separate **actual GPU** regression reproduces
the count transition (26/25), reads the real kernel matrices, and verifies the
new matrix change is below 0.001 inverse meters while the old change exceeds
0.5. It also verifies unchanged integrated quadrature weights and zero GPU
diagnostics. Kernel readback buffers declare copy-source usage explicitly.

## How much of the actual capture changes?

The analysis of all 51,871 positions in `liquid-muted-green-motion` finds:

- 383 particles in the continuous transition, 58 purely isotropic and 51,430
  fully anisotropic; this is a localized change, not a solution to every lump.
- 67 particles have raw neighbor counts from 20 through 30.
- 254 kernels change an axis by more than 1 cm and 140 by more than 5 cm after
  the existing prefilter. The maximum difference is 89.70 cm in a sparse case.
- Particle centers and quadrature weights are exactly unchanged in the CPU
  comparison. This does **not** prove invariant isosurface volume or river mass.

See `liquid-muted-green-motion/kernel_transition_analysis.json`. Both fits use
the same actual positions; these are kernel support changes, not measured wave
height changes. The small affected fraction explains why the overall surface
still looks lumpy after fixing this discontinuity.

## Runtime and performance

`liquid-continuous-kernel-motion` uses the selected muted-green optics and
continuous kernels. The report confirms the requested runtime mode. All 714
simulation dispatches and GPU clock increments are accounted for over 12 s.
Live positions, finite fields, active/paused foam transport and exact sampled
secondary bed/domain contact pass with unchanged tolerances. Final sampled
spray inside water is **0 / 13,046**; all 13,053 bubbles are inside. Foam absolute
interface distance p95 is 0.944 cm. Thirty distinct captured frames show motion.
RHI validation logs no engine errors. This is not complete trajectory/contact
coverage or a 60-second stability test of this new variant.

The uninterrupted benchmark has 480 intervals: mean **26.189 ms**, p95
**28.580 ms**, p99 **29.930 ms**, maximum **33.625 ms**. Reconstruction GPU mean
is **5.464 ms** (density 4.667, distance 0.581, foam/copy 0.216). No timing-window
readbacks/image exports or logged engine errors. Compared with the separate
prior 26.038 ms / 5.410 ms run, this does not establish a speedup; it is slightly
more costly on average. Neither run is packaged-game or whole-scene acceptance.

165 numerical tests pass. All **16** engine liquid tests, including the new
actual GPU continuity test, pass without test warnings/failures under RHI
validation in `engine-liquid-sparse-transition`. The initial C++ test build
needed a const array view correction; the subsequent build succeeds.

## Ray-tracing check and limitations

Before editing kernels, `audit_liquid_ray_hits.py` compared the inherited marcher
against dense sign-crossing scans of the captured field at 1 cm and 5 mm steps.
At 5 mm, both found 5,308 hits among 13,824 camera rays, with no missing first
crossings or later hits beyond 2 cm. Common error p95 is 0.385 cm. A grazing-ray
outlier remains 130.55 cm **earlier** than the dense crossing; dense scans can
miss very thin/grazing intersections, and the inherited hit tolerance can also
accept near-zero samples. This is not exact intersection proof. Terrain
occlusion and GPU filter rounding are not modeled. No raymarch change was made
because these samples did not establish it as the cause of the broad lumps.

## Next required work

Actual motion still has gelatinous shapes, regular ripples, coarse breaking
sheets and rectangular fixture faces. The new switch removes a demonstrated
local discontinuity, not the dominant dense-surface/flow problem. Continue
primary free-surface shape and source/outlet/roller physics, preserving the
current-stage and foam fixes, then continuous playable integration and full-scene
performance. Do not substitute more whitening or a second surface. Keep the
source-provenance and inferred-bed uncertainties explicit. South Fork remains
incomplete, followed by Colorado -> Pacuare -> Futaleufu and the remaining
river/crew/cleanup/release queue. No saved production promotion or commit.
