# South Fork 3D-water terrain and flux handoff

September 8, 2026. Progress toward the actual river integration, not a new
photorealism claim or completion of South Fork. No production map is changed.

## Exact local collision surface

`build_south_fork_liquid_window.py` clips the existing registered-XY candidate
at station/lateral zero. Its 24 m square top retains the original triangles,
splitting only at the boundary without smoothing or replacing the rock shape.
It contains 201 captured rock returns. The source's submerged bed and connecting
faces remain inferred; real Troublemaker identity is still unverified.

The signed-distance solid has artificial side/bottom closures outside the
20 m fluid domain. These are not bathymetry. The artificial bottom is below
the fluid domain floor. The source frame is a rigid rotation of
158.43478935409635 degrees, with local origin at engine (0,0,350) cm, not a
curved-axis deformation. The top uses 5,032 triangles; the closed solid uses
6,334 triangles and 3,169 vertices. Every clipped top-triangle centroid agrees
with the independent source sampler within 7.9048e-14 m.

Source geometry SHA256:
`4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
New solid SHA256:
`3a7794fde65d02ef7c4bc8fd88e1a45bf258e4f41a729be439627809182cc9b7`.
Source package: `unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908`.
Engine asset: `/Game/RaftSim/Environment/SouthForkLiquidWindow20260908/SM_SouthForkLiquidCollisionSolid`.
Engine asset SHA256:
`1ce164f5de059d7bf08373b65168cfac45d7f1feb3bf41cb3e8259de4a0dff79`.

Unreal import8394 exited0. All 5,032 top-triangle centroid ray probes pass,
maximum height error 0.00120595 cm in the actual registered transform. Only the
new asset was saved; no scene was saved. Import retains FBX smoothing/tangent
warnings (the collision solid currently has no proper UV/tangent authoring),
and a deprecated visibility-query enum warning. These are not a clean visual
asset import. The initial Python generator failed its manifold check because
the bottom winding was reversed; the check caught it before any output package
was written. Corrected manifold, surface-preservation, sampling, uniform-flux,
dry-conflict, and missing-source-coverage tests all pass (six unittest tests).
The bundled Python has no pytest; the initial pytest invocation failed and was
replaced by the same tests through the standard-library runner, not skipped.

Build54029 succeeded. Fresh engine suite87361 reports five clean successes,
zero failures/warnings in 6.57 s (`engine-liquid-terrain/index.json`). It verifies
actual generated SDF data, not only build settings: indirection 37x37x37,
19,136 bricks, 455,072 resident mip bytes, not a two-sided sheet. It does NOT
prove signed-distance accuracy or GPU particle separation against this terrain.

## Interpolated boundary rejected, numerical flux exposed

The first 20 m handoff samples coarse momentum and stage at 0.5 m intervals,
then checks depth against the exact clipped bed. It finds two dry/nonzero-flux
conflicts and explicitly records `boundary_handoff_ready=false`. Its aggregate
in/out values (47.7688/50.1248 m3/s) are not a conservative solver face audit.
They must not be supplied as accepted 3D boundary conditions or silently masked.

The native solver now exposes `inspect_numerical_mass_flux_grid()` and the CLI
flag `--inspect-face-fluxes`. The output uses the exact same hydrostatic MUSCL
reconstruction and Riemann fluxes as stepping, including prescribed external
boundaries. It is read-only (`dt=0`, scratch state), with ny x (nx+1) x-faces
and (ny+1) x nx y-faces in m2/s, positive along each grid axis. No cell-velocity
interpolation substitutes for a face flux. Normal stepping allocates no new
flux grids. The public native test compares dimensions, uniform interior flux,
integrated boundary flux and unchanged state/time.

A separate Release build preserves the old hydraulic binaries:
`tmp/south-fork-liquid-flux-build-20260908/Release/raftsim_water_solver.exe`.
SHA256 `0cd6cefbe75173e74dab8266d3230764cc5cfd6d9a614fe847001131f15bf153`.
Build72739 and all three CTest fixture suites succeed: wet/dry shoreline,
lake-at-rest balance and transcritical bump. The engine-linked native archive
has not been replaced, and no new performance claim follows from this build.

`audit_south_fork_liquid_flux.py` verifies the existing final-state audit package
against all four engine h/u/v/bed arrays before exporting numerical fluxes.
The local control volume uses actual finite-volume faces -10.5..10.5 m in both
axes. This 21 m box is NOT the same boundary as the earlier rejected 20 m box;
do not attribute their entire difference to interpolation alone.

- Net numerical inflow: 0.0311408647374 m3/s.
- Measured local volume derivative after a 1e-6 s step: 0.0311395150800 m3/s.
- Absolute conservation error: 1.34965736e-6 m3/s, within the unchanged 1e-3
  audit tolerance.

`liquid-native-face-flux/report.json` and `native_faces.npz` retain the full
arrays, per-face discharge, geometry/field/solver hashes and the tiny-step
output. Audit exited0. This proves a conservative numerical handoff source,
not calibrated real-world discharge or a driven FLIP simulation.

## Next work

Use the native grid-aligned faces to build the actual inlet/outlet handoff,
resolve partial wet support against the exact bed without losing flux, and
drive the terrain-colliding 3D water. Validate source/retirement volume, stage,
single visible surface and raft support in South Fork. Verify the terrain SDF
with actual particles; clean the collision-solid import warnings. Optics, foam,
breaking crests, animation and performance remain open. Do not substitute a
sphere or another tank test for this river integration. No production promotion,
final commit, goal completion or change to the full remaining-work scope.
