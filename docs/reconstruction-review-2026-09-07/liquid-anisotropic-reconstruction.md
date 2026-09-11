# Anisotropic surface reconstruction reference — September 8

Status: numerical prototype only. **Not renderer-integrated, not accepted, and
not a completion of South Fork or the remaining scene queue.** No saved engine
asset, physics setting or production rendering resolution changed.

## Basis and implementation

The active compiled liquid reconstruction forms a minimum-distance union of
particle spheres followed by separable convolution. The resulting rounded
surface motivates evaluating neighborhood-shaped kernels rather than another
foam-color multiplier. Primary reference: Yu and Turk,
[Reconstructing Surfaces of Particle-Based Fluids Using Anisotropic Kernels](https://faculty.cc.gatech.edu/~turk/my_papers/sph_surfaces.pdf).
The downloaded paper's equations and illustrations on pages 3–5 were inspected,
including rendered pages 4–5. Source SHA256:
`39351004F6619BBCE3BF9B35B45B497BD1A32105DEC6A3B78B94CA0213B61696`.

`physics/scripts/liquid_anisotropic_surface.py` implements a NumPy reference:
weighted neighborhood covariance, bounded eigenvalue aspect ratio, render-only
center averaging, spherical sparse/degenerate fallback, and summed normalized
anisotropic cubic kernels. It does not move simulated particles. The covariance
scale uses the analytic uniform-neighborhood covariance rather than copying the
paper's unit-dependent example constant. Sparse centers remain unshifted.

Two weighting modes are retained explicitly. Constant nominal FLIP volume is
the initial diagnostic. The corrected reference estimates equal-mass local
density from original particle positions and uses inverse number density as
the surface quadrature weight. This is not a physical mass-budget correction.
The field is density, **not a signed-distance field**; it must not be substituted
directly into the current SDF ray marcher.

## Actual captured particles

All runs use the same 80,629 particle readback from the prior 60-second GPU run:
`liquid-advected-foam-60s/terrain_3600_particles.json`, SHA256
`4fa693dc140af6f757194b57ffbad06f83d847eaf6d13e278d5c7d6d5c9920ce`.
Radius is 0.4 m, support 0.8 m, center averaging 0.9, maximum axis ratio 4.
These controls are research candidates, not photographic calibration.

| Reference | Grid | Density maximum | Integrated density, m³ | Iso-0.5 voxel volume, m³ |
|---|---|---:|---:|---:|
| Constant nominal weight | 136×136×48 | 1112.29 | 703.95 | 324.59 |
| Local-density normalization | 136×136×48 | 38.10 | 437.87 | 317.27 |
| Same normalized kernels, finer sampling | 272×272×96 | 253.91 | 441.93 | 318.94 |

The density maximum is a sampling-sensitive interior diagnostic, not surface
quality. The normalized kernels' analytic integral before boundary clipping is
441.76 m³. This is a quadrature consistency check, not measured water storage.
32,725 kernels have a minor axis below the coarse voxel size; 3,315 remain below
the finer voxel size. One coincident/degenerate neighborhood uses the fallback.
Median center displacement is 9.20 cm; maximum is 46.89 cm. No displacement is
fed back to the fluid simulator.

`compare_liquid_surface_reconstruction.py` checks identical particle kernels and
compares the highest interpolated liquid-to-air crossing on nested grids. It
does not invent crossings for empty or upper-boundary-clipped columns. Among
13,763 common columns, refinement changes height by 8.02 cm RMS; median absolute
change is 2.59 cm, 95th percentile 10.02 cm, maximum 1.18 m. There are 249
coarse-only and 59 fine-only columns after requiring complete fine neighborhoods.
Some highest crossings may be detached droplets rather than the main liquid
body. Iso-volume changes by 0.525%, which does **not** establish surface or
temporal convergence. These are fixed-particle resolution comparisons, not
proof of the cause of the user's runtime jumping.

Artifacts are in `liquid-anisotropic-reference-60s`,
`liquid-anisotropic-density-normalized-60s`, and
`liquid-anisotropic-density-normalized-60s-refined`. The latter includes
`grid_comparison.json`. CPU reconstruction took 18.60, 22.44 and 24.94 seconds
respectively. These are offline reference timings, never game-frame rates.

## Verification and next work

56 focused `test_liquid*.py` tests pass (1.371 seconds). Twelve are reconstruction
tests: finite sparse/coincident fallback; sheet anisotropy; source-position
immutability; rotation/translation/unit equivariance; kernel integral;
ellipsoid quadrature; duplicate-sampling invariance; validation; upper crossing;
exact affine-surface grid comparison; disconnected-component analysis; and
unshifted-center policy isolation. No new C++ build was needed for these
Python-only changes. Prior actual-engine tests remain historical, not rerun.

Next: test coherent body/crest preservation and temporal sampling, then build a
distance-correct, bounded-cost rendering candidate and inspect actual engine
motion. Do not raise production voxel resolution based on this offline test.
Free-surface foam, native/3D exchange/storage, full-scene integration,
performance and photographic acceptance remain open. Colorado, Pacuare,
Futaleufu, other-scene water, crew, cleanup and release remain queued.

## Controlled crest/elevation audit and unshifted candidate

`audit_liquid_reconstruction_features.py` creates deterministic 19,200-particle
volumes with a prescribed flat surface or a 0.2 m amplitude, 3 m wavelength
crest. It also translates the identical crest particles by one-third of the
0.1 m raster spacing. These are controlled reference cases, not engine frames.
The source volume boundary is specified independently of reconstruction.

The initial center-averaged kernel method lowers the flat surface by17.37 cm
and the crest surface by18.16 cm on average. Its very low flat-surface ripple
is therefore **not sufficient acceptance**: it would disagree with water-level
support. This candidate is rejected for promotion.

The unshifted candidate retains covariance-shaped kernels and density weights
but disables center averaging. On the flat test its mean height error is
+2.04 cm, versus +3.42 cm for the isotropic density baseline. Its fitted crest
amplitude is20.19 cm versus the prescribed20 cm (isotropic19.47 cm). After the
subvoxel translation it is20.29 cm. Mean crest elevation error is+1.84/+1.86 cm;
debiased error1.06/1.05 cm. There are no missing interior crossings in these
tests. Results are in `liquid-anisotropic-controlled-features` and
`liquid-anisotropic-controlled-features-unshifted`.

However, the actual South Fork particle replay remains unresolved. Unshifted
coarse/refined reconstruction gives iso-volume382.10/389.87m³, a2.03% difference.
Main-body analysis finds352/186 six-connected liquid components. After removing
detached components **only from the diagnostic copy**, main-body top height
still differs11.91 cm RMS between grids (95th percentile25.01 cm,max1.36 m).
Removing droplets therefore does not explain away the resolution sensitivity.
The shifted candidate similarly retains8.42 cm main-body RMS change. No particles
or rendered components were deleted by this analysis.

Actual unshifted outputs: `liquid-anisotropic-unshifted-60s` and
`liquid-anisotropic-unshifted-60s-refined`, including the latter's
`grid_comparison_components.json`. All kernels remain at original particle
positions. The report explicitly records disabling the paper's center averaging.

Next candidate should address kernels below raster resolution with a derived
sampling footprint, checking both elevation/crest preservation and convergence.
Do not compensate for the17 cm bias by moving water or the boat, substitute
density for signed distance, or globally increase resolution/performance cost.
Actual GPU integration, engine motion and all acceptance gates remain outstanding.
