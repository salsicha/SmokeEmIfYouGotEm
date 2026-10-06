# Resolution-aware reconstruction and engine snapshot — September 8

Status: **offline reconstruction reaches the actual engine renderer; live
reconstruction, performance and visual acceptance remain incomplete.** No
production promotion or saved engine-asset change. The complete task queue
remains active.

## Sampling-aware kernel reference

`liquid_anisotropic_surface.py` now supports an explicit metric sampling
footprint. The unit-support cubic kernel has per-axis covariance0.075; a box
footprint of width f has covariance f²/12. Adding these moments gives broadened
ellipsoid axes sqrt(axis²+f²/0.9), without moving kernel centers or changing their
quadrature weights. This is a moment-matched approximation, **not exact box
convolution**, and preserves kernel integral rather than isosurface volume.

The same80,629 captured particles were reconstructed on136×136×48 and272×272×96
grids with a fixed1/6m footprint. All kernels then exceed the coarse voxel size.
The finer-grid integral441.769m³ closely matches the kernel integral441.764m³;
neither is calibrated physical water storage. Iso-volume424.119/428.493m³ changes
1.031%. Main-body height changes8.29cm RMS, median1.69cm,95th percentile16.26cm.
This improves the unfiltered11.91cm RMS but does not establish convergence.

Controlled19,200-particle tests retain the prescribed20cm crest at20.156cm
(20.137cm after a1/30m translation). Flat-water bias is+1.94cm, crest bias+2.24cm.
No particle positions are changed. The earlier center-averaging variant remains
rejected for its17–18cm elevation error.

Artifacts: `liquid-anisotropic-prefiltered-60s`,
`liquid-anisotropic-prefiltered-60s-refined`, and
`liquid-anisotropic-controlled-features-prefiltered`.

## Density is not a distance field

`liquid_density_surface.py` extracts the density0.5 interface using a consistent
six-tetrahedron cube decomposition. It computes metric distances to those
triangles within a0.5m band, with signs from the density field. This is distance
to the piecewise-linear tetrahedron surface, not to the exact trilinear
isosurface. It does not invent a second plane or move the simulation.

The coarse captured field produces749,448 triangles. Offline conversion takes
183.49seconds; **not suitable for per-frame use**. Redistancing changes the
interpolated top crossing by8.78mm RMS (95th percentile18.26mm), measured over
14,859 common columns. Values are finite and retain the density classification.
The large triangle count warrants an interior-void/solver-occupancy audit before
designing the live GPU path; top-surface smoothness alone is not sufficient.

Output: `liquid-anisotropic-prefiltered-60s-surface/surface.npz` and
`surface.rgba16f`. R contains centimeters of signed distance; GBA are zero for
this geometry-only experiment. Texture SHA256:
`4ac535ad2fd9df8f2f94662d2795c81759fe6ecd542c1661be83ba4151cc9d8c`.

## Actual engine comparison

`RaftSim.LiquidSurfaceSnapshotReview` accepts only a scoped diagnostic source,
an unused report directory, the expected domain/dimensions, finite distance
data and one frozen transient liquid material. It creates an unsaved volume
texture, verifies every RGBA16f voxel against an actual GPU readback, and binds
that texture to the existing single-surface renderer. It does not change
simulation grids, stages, particles or saved materials. Runtime material
diagnostics now record texture bindings, checking they survive to capture.

The first capture, `liquid-surface-snapshot-engine`, successfully verified
rendering but compared a fresh simulation with a prior-state reconstruction.
It is retained as an integration check, not a strict geometry-only A/B.

The definitive comparison is `liquid-surface-snapshot-exact-source`:

- `prepare_liquid_surface_baseline.py` preserves the original captured renderer
  SDF's red channel bit-for-bit and clears unused channels for a foam-off control.
- Both baseline and reconstruction reference particle capture SHA256
  `4fa693dc140af6f757194b57ffbad06f83d847eaf6d13e278d5c7d6d5c9920ce`.
- The camera, lighting, scalar/vector material parameters and optical controls
  are identical. Both texture uploads verify all887,808voxels exactly on GPU.
- `optics_00_particles.json` binds `T_RaftSimOfflineSurfaceSnapshot_0`;
  `optics_01_particles.json` binds `_1`, matching their binding reports.
- `audit_liquid_surface_snapshot.py` independently checks source hashes,
  bindings, controls and material uniforms. `geometry_ab_audit.json` passes;
  114,462pixels change by more than two channel levels.
- Both native images were visually inspected. The reconstructed surface has
  finer breakup but still looks rounded/plastic. Both expose rectangular
  diagnostic-window sides against angular, untextured diagnostic terrain.
  Neither is photorealistic whitewater. Foam was intentionally disabled; this
  test does not establish foam behavior or live animation.

![Original captured SDF, geometry-only control](liquid-surface-snapshot-exact-source/optics_00.png)

![Reconstructed SDF, identical source and optics](liquid-surface-snapshot-exact-source/optics_01.png)

Capture wall time88.94seconds includes blocking diagnostics and is **not FPS**.
The test-report hardware survey names integrated Radeon graphics, but the
authoritative D3D12 log selects adapter0, NVIDIA RTX3060 Laptop GPU (5994MB).
No adapter setting was changed based on the misleading survey label.

## Verification and next action

- Latest build passes,12.40seconds; first viewer build27.99seconds.
- `engine-liquid-surface-snapshot/index.json`:10 clean successes,0warnings or
  failures,23.738seconds. This precedes the small baseline-kind extension;
  the subsequent exact-source engine capture exercises that extension.
- 63focused `test_liquid*.py` tests pass,1.621seconds. New tests cover footprint
  covariance, immutable source data, exact affine distances and outward winding,
  closed-sphere edge incidence, triangle distance regions, constant fields and
  bitwise preservation of the captured baseline.
- Saved Niagara asset, review map and `.uproject` SHA256 identities match the
  previous checkpoint. No production resolution increase, physics change,
  generated image replacement, or commit.

Next: inspect reconstructed internal interfaces against the actual fluid/air
classification; then implement a bounded-cost live reconstruction path and
surface-consistent aeration. The offline triangle raster is a reference, not
the runtime implementation. Native exchange/storage, full-scene carrier
handoff, shore continuity, performance and photographic/motion gates remain
open. Subsequent river, crew, cleanup and release tasks remain queued.
