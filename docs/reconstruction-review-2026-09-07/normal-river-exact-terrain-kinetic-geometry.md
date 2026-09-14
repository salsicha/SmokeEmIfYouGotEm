# Exact-terrain pressure kinetic geometry — September 14

The previous turn completed necessary flat-bed 2-D research controls. This turn
adds the missing **local terrain-dependent kinetic coefficients** needed to
couple that pressure model to original registered source triangles. It does not
yet choose a shared intercell velocity derivative or complete the nonlinear
bed-force, dry-front, time or gameplay coupling.

## Geometry consumed without changing the source

For a constant local horizontal velocity u, local divergence d, and original
triangle bed gradient b, the existing vertical kinetic form is

```text
integral_wet [h (h*d - 1.5*b.u)^2 + .75*h*(b.u)^2] dA
```

For the jet `(d,u_x,u_y)`, its Gram blocks are
`G_dd=integral(h^3)`, `G_du=-1.5*integral(h^2*b)` and
`G_uu=3*integral(h*b*b^T)`. These are coefficients for the existing completed-
square pressure form, not newly fitted pole weights or a different dispersion
law. At constant depth on a flat bed, the only nonzero coefficient is `area*h^3`,
matching the prior flat-column kinetic geometry.

Each source triangle is clipped by the datum-relative water level using positive
wet pieces. A six-node positive Duffy/Gauss rule integrates the resulting cubic
polynomials exactly up to floating-point arithmetic. The implementation factors
the two positive squares directly. It does not clip negative eigenvalues,
smooth source slopes, move a bed point, or introduce a minimum water depth.

The fixed-terrain volume derivative follows
`d/deta integral(h^k) = k*integral(h^(k-1))` and `dV/deta=wet_area`.
The original integrand vanishes at h=0, so there is no moving-edge boundary
term. An exactly level shoreline with no two-sided derivative is explicitly
rejected. Exactly dry volume is also rejected; no inverse dry mass is fabricated.
This coefficient derivative is **not** the complete normalized pressure-metric
derivative: the future intercell derivative and normalization must also change
consistently with volume.

## Provenance survives clipping

`cell_triangles` can now return the original source-face index of each clipped
piece. `SubcellGeometryPatch` retains those indices as immutable metadata.
Clipping coordinates, triangulation, original vertices and all previous return
values for callers that do not request IDs remain unchanged. The audit traces
each wet piece back to its original vertex authority codes, without averaging
or upgrading those codes to measurement authority.

The registered source includes **uncalibrated inference**, not just captured
geometry. For the actual patch, wet volume by source-triangle vertex codes is:

| Vertex codes | Authority | Wet volume, m3 |
| --- | --- | ---: |
| 2 | Inferred submerged prior | 498.179280 |
| 2,5 | Prior / inferred connecting flank | 18.877443 |
| 5 | Inferred connecting flank | 20.743944 |
| 3,5 | Exposed-rock return support / inferred flank | 1.529754 |
| 3 | Exposed-rock return support at all vertices | 1.305191 |
| 3,4 | Return support / interpolated support | 0.105184 |

A source-supported vertex does not turn a mixed triangle or submerged bathymetry
into a survey measurement. Exact integration preserves the registered geometry;
it does not calibrate or prove that geometry's inferred submerged shape.

## Actual 600-second South Fork state

The audit uses the same 16x16, one-metre cells beginning at
`[-5438.999999998952,3593]`, original atlas volumes, registered triangle topology,
and datum mapping. Hydraulic/captured center-height agreement remains 1.42e-14 m.
No water state is remapped, cooked further, reset or promoted.

All **255 positive-volume cells** pass exact-volume and local kinetic-tangent
controls. The remaining cell, index158, is dry and explicitly unsupported by this
positive-volume primitive. Maximum relative volume reconstruction error is
7.24e-16; the maximum scaled centered-difference check of the analytic kinetic
volume derivative is 1.15e-10 (this numerical derivative check is not an evolved
energy gate).

The new coefficients expose terrain variation that a single aggregate value
cannot retain:

- Replacing triangle slopes with their exact wet-volume-weighted mean loses a
  median 4.04% and p95 72.43% of `trace(G_uu)`; maximum loss is 99.99992%.
- This is not just a nearly dry-cell effect. Fully wet cell112 stores 1.22362 m3
  and loses 99.9468% of that slope-dependent coefficient under the mean-slope
  comparison.
- Replacing the wet depth distribution with its mean loses a median 0.0607%,
  p95 57.52%, and maximum 67.25% of the cubic-depth coefficient.

These are **coefficient comparisons**, not actual total flow-energy losses or
predicted wave-height changes. The mean-slope comparison is a well-defined
aggregate diagnostic, not a claim that it is the actual native coarse-slope
stencil. They establish why retaining the fine geometry is necessary; they do
not establish that this alone will fix the rendered rapid.

## Verification and remaining coupling

The final targeted suite passes **62 tests** in 5.99 seconds. Fifteen new tests
cover analytic depth moments across all wet branches, positive kinetic factors,
volume-derivative refinement, triangle subdivision invariance, flat and thin-water
limits, nonsmooth/dry rejection, opposing-slope information loss, and original
source-face provenance. Existing storage, shared-face pressure, relative-stage,
energy and transport regressions remain passing. Prior two-pole default-path
energy failures remain open; no previous required gate is waived by these tests.

```text
python -m pytest physics/tests/test_subcell_pressure_kinetic_geometry.py physics/tests/test_triangle_cell_storage.py physics/tests/test_triangle_face_section.py physics/tests/test_subcell_energy_flux.py physics/tests/test_subcell_relative_stage.py physics/tests/test_subcell_mechanical_energy.py physics/tests/test_subcell_implicit_transport.py physics/tests/test_subcell_geometry_patch.py physics/tests/test_subcell_drain_event.py -q
python physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report FRESH_PATH
```

Final audit: `tmp/south-fork-subcell-kinetic-geometry-v3-20260914.json`, SHA256
`706ae529224a5a99f71a34fc1d183b7a280610bdd0c92b7cf9c0b65e0638c20d`.
Final tests: `tmp/subcell-kinetic-geometry-final-v2-20260914.xml`.
The v1 audit has the same numerical coefficients but predates per-piece source
authority reporting. V2 added provenance; v3 also explicitly rejects negative
source volumes rather than classifying them as unsupported dry cells. Numerical
results are unchanged, and v3 is the final provenance-bearing record.

All 464 protected scene/source/actor hashes were checked unchanged. This turn
does not change an Unreal map, material, water atlas or runtime physics default.
No new visual pass, FPS result or scene acceptance is claimed.

Next: assemble the shared wet-face velocity derivative and its adjoint against
these exact local factors, then connect both original pressure poles and the
complete metric/bed-force work. Include the actual dry cell and physical patch
boundaries; a positive periodic proxy is not a replacement for that coupling.
Finite-time, wet-front, open-boundary, refinement and native/shared-surface
qualification remain required, followed by the full later-river/crew/release
scope. The playable South Fork rapid and 30 FPS gates remain unfinished.
