# Separated wet-pool pressure on exact terrain — September 14

The preceding turn supplied exact local terrain-dependent kinetic coefficients.
This turn connects those factors through shared wet source faces and both
original pressure poles. Crucially, the actual patch cannot use one pressure
unknown per wet Cartesian cell: three cells contain two disconnected pools.
The implementation now represents those pools separately at the fixed snapshot.
It is **not** yet a nonlinear time-evolution or gameplay solver.

## Source topology establishes the pressure regions

Connectivity follows original source triangle vertex IDs. Two wet triangles
connect only if their common source edge has a strictly positive wet length
inside the cell footprint. Predicates use exact rationals of the represented
source coordinates and datum-relative stage. Point contacts, exactly dry edges,
outside-footprint edges and zero projected edge lengths are not bridges.
No rounded-coordinate welding or small-water cutoff is introduced.

The actual 600-second, 16x16 South Fork patch has 255 wet cells and **258 wet
components**. Cell158 is dry. The three split cells are:

| Cell index | First pool volume, m3 | Second pool volume, m3 |
| --- | ---: | ---: |
| 157 | 2.54430936e-9 | 1.43785434e-6 |
| 236 | 0.00697039789 | 0.00022583668 |
| 238 | 0.09964391954 | 7.42567242e-8 |

The small pools are retained, not discarded. Each component gets its original
clipped triangles, immutable source-face IDs and exact local kinetic factor.
The original cell velocity supplies the initial component momenta. Reassembly
differs from the source by at most 1.78e-15 m3 in volume and 4.45e-15 in integrated
momentum. These are reported storage-inversion/rounding errors, not corrected by
rescaling or assigning a residual to a selected pool. The sum of component Gram
matrices agrees to 3.91e-14; their wet-area-weighted volume derivatives agree to
2.14e-14.

This partition is valid only for the fixed wet topology. It records the adjacent
source-height event interval and rejects an exactly coincident topology event.
There is no implemented time-step crossing, merger/split or newly wet pool
creation mechanism. Different component levels must eventually evolve
independently; treating their initial equal parent stage as a permanent constraint
would reconnect them incorrectly.

## One shared wet-column coefficient and its exact adjoint

For each shared source-face subsegment, the pressure trace uses

```text
H_face = integral_common_wet 2*h_left*h_right/(h_left+h_right) ds
```

The rational integrand is evaluated through its logarithmic antiderivative.
A convergent small-argument series prevents numerical log subtraction loss;
this is an arithmetic evaluation choice, not a wet-depth threshold. Tests cover
equal stages, distinct datum-relative stages, exactly dry sides and representable
depths down to 1e-150.

For an internal face oriented along Cartesian component j, the contributions to
the two local velocity divergences are

```text
D_left  += H_face/(2*V_left)  * (u_right,j-u_left,j)
D_right += H_face/(2*V_right) * (u_right,j-u_left,j)
```

The operator's transpose is assembled from exactly those same coefficients.
On a flat Cartesian grid `H_face=2*h_left*h_right/(h_left+h_right)*face_length`,
which reduces to the original reconstructed D_h depth weights, including
variable depth. At exterior reflecting walls, zero face-normal velocity gives
the explicit contribution `-normal_sign*A_face*u_j/V`.

Face pieces are tagged by their component owner. The graph intersects both
owners' wet coverage and evaluates each common subsegment once. Summed shared
columns match the unsplit original face integration to 6.42e-16; wall columns
match to 4.44e-16. The existing 1e-9 source-face geometry-agreement tolerance is
retained, without moving or welding coordinates to satisfy it.

## Same two poles, actual terrain factors

Let C map normalized pool velocity q to the local jet
`(D(q/sqrt(V)), q_x/sqrt(V), q_y/sqrt(V))`. The previous exact positive local
factors F then give the pressure matrix

```text
A_length = I + length * C^T F^T F C
S = (1-sum(weights))*I + sum(weights_j * A_length_j^-1)
```

Both lengths and weights come directly from the existing two-pole constants.
The solve uses the unchanged 40-iteration range-CG implementation and true
residual gate 2e-5, with exact local 2x2 block preconditioning. It does not replace
the solve with a dense answer or use the later flat-only FFT preconditioner on
nonflat terrain.

The actual graph contains 1,839 shared wet subsegments and 248 reflecting-wall
subsegments. There are **zero direct same-cell pool connections**. A synthetic
rock-ridge test independently verifies that a pressure impulse on one isolated
side produces exactly zero response on the other side. Indirect connections
through real wet paths in neighboring cells are allowed.

Both actual-source poles pass:

| Pole length | True relative residual | Scaled error versus independent dense solve |
| --- | ---: | ---: |
| 0.4052787713439809 | 4.40190e-13 | 6.73140e-13 |
| 0.03916567310046354 | 2.59578e-16 | 1.26190e-15 |

The independent bounded audit assembles the full matrix from local Gram tensors,
separately from the factor-action path used by CG. Maximum scaled matrix-action
discrepancy is 4.71e-16. The right-hand side is explicitly a source-velocity-shaped
normalized **probe**, not the river's derived nonlinear acceleration. No new
water state or trajectory is generated by this test.

## Tests, provenance and remaining work

The final targeted suite passes **72 tests** in 7.13 seconds. Ten new controls
cover pool partitioning, original-source edge connectivity, point/dry isolation,
both original flat variable-depth operators, the oblique two-pole linear
response, factor adjoints and positive energy, exact local pressure blocks,
high-precision harmonic-face integration, and dry/topology-event handling.
All 62 previous targeted geometry/storage/energy/transport regressions also pass.
This does not waive prior nonlinear energy failures or qualify finite-time
wetting, breaking or open-river evolution.

```text
python -m pytest physics/tests/test_subcell_wet_pool_pressure.py physics/tests/test_subcell_pressure_kinetic_geometry.py physics/tests/test_triangle_cell_storage.py physics/tests/test_triangle_face_section.py physics/tests/test_subcell_energy_flux.py physics/tests/test_subcell_relative_stage.py physics/tests/test_subcell_mechanical_energy.py physics/tests/test_subcell_implicit_transport.py physics/tests/test_subcell_geometry_patch.py physics/tests/test_subcell_drain_event.py -q
python physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --pool-pressure --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report FRESH_PATH
```

Final audit: `tmp/south-fork-subcell-pool-pressure-v3-20260914.json`, SHA256
`9467892e6090941b525003a93f04739c3d73ca8269bf41f3f1550f70cfaa655a`.
Final tests: `tmp/subcell-pool-pressure-final-v1-20260914.xml`.
The pressure audit exits 1 if its solve, independent solution, face coverage or
partition-preservation checks fail; exit 0 still leaves gameplay acceptance false.

All 464 protected scene/source/actor hashes were checked unchanged. Original
authority codes remain attached to source triangles: much of this patch is
inferred submerged bed or connecting flanks, not surveyed bathymetry. No inferred
triangle is promoted to measured status by exact integration or pressure tests.

Next required work is the **complete volume-dependent metric and nonlinear
bed-force/advection work** on this pool graph, coupled to conservative pool
storage/fluxes. Add explicit topology-event handling and wetting/drying, then
finite-time, open-boundary, refinement and native/shared-surface qualification.
No map, material, atlas or runtime physics default changed this turn. The actual
rapid's terrain/flow appearance, breaking/froth and 30 FPS goals remain open,
as do the later rivers, crew and release requirements.
