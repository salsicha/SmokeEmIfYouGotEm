# Native-face pressure-boundary drive

September 8. This remains an isolated South Fork physics candidate, not a
finished scene or photorealistic water. No production asset replacement or commit.

## Implemented

`build_south_fork_liquid_grid_boundary.py` verifies registered terrain and
hydraulic hashes, reads the audited native face fluxes, and transfers each
native one-metre face total onto overlapping wet computational-face support.
Dry columns receive no flow. The first attempt uniformly distributed flux and
failed on unresolved shallow columns; the wet-area transfer preserves native
face totals where represented. Two dry south-face residuals of
1.4903933587e-8 and 2.4906929000e-8 m³/s are explicitly unresolved, not replaced
by phantom wet cells. Each is below 1e-7 m³/s (less than float32 epsilon at
1m³/s); the residual is recorded and tested, not concealed in an exactness claim.

The profile uses bed and stage at the actual native face, not terrain outside
the physical window. Its ghost support has 64 columns per face and 24 vertical
cells, dx=0.328125m, dz=8/24m. Normal velocity is remapped signed flux divided
by the discrete wet face area. Both incoming and outgoing flux are prescribed;
this is **not** outgoing pressure/stage coupling. Wet vertical support uses the
hydraulic stage. Native totals west/east/south/north are approximately
41.412585/-45.103418/2.247995/1.473978 m³/s after the tiny recorded residual.
Peak prescribed normal speeds are 2.028/3.088/1.407/0.841m/s. These are numerical
model targets, not measured river discharge.

Profile `unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908/grid_boundary_profile.json`
SHA-256 `40d4201efe001117fb062c0589c42dfb13aca75c018328256c3b7c36e763b9ed`.
Four header vectors describe orientation and dimensions; 4x64 records store
face bed, stage and normal speed. Submerged bed is still inferred and rapid
identity is not yet accepted.

The transient `driven-boundary` console variant inherits the two-cell grid
margin, registered wet initialization, full neighbor gather, correct transfer
basis, and shared exact terrain contact. Only pressure-boundary queries outside
the physical 21m faces are replaced with wet ghost SOLID cells carrying the
prescribed grid-local normal velocity. Existing pressure RHS and projection
consume that velocity. Real terrain inside the physical window remains
stationary; particle contact continues using actual registered triangles, not
the virtual boundary. Source injection and physical retirement box are unchanged.

## First actual-GPU result

`liquid-terrain-driven-boundary`, log `CaptureLiquidTerrainDrivenBoundary.log`:
720 steps/12s, complete=true, 27.90s diagnostic wall time (not gameplay timing).
At12s: 98,224 live particles, zero nonfinite positions or velocities, zero
sampled bed penetration, 63 outside the physical domain. Median speed76.827cm/s,
mean79.775cm/s. Upstream/centre/downstream counts28,008/28,785/14,259, mean
X velocities69.202/56.873/93.274cm/s. The preceding unforced margin variant had
negative mean X upstream/centrally and only23,576 live particles. Actual
pressure-boundary drive restores downstream motion in this short comparison.

Independent local32.8125cm analysis-bin maximum is121 at12s, rather than the
6,827 pile-up without the margin. It is not a direct NQ occupancy readback.
Live count rises from77,236 at0.1s to98,224 at12s: storage is not settled or
calibrated. A longer run is required. The inspected fixed opacity-one image
shows greater connected coverage but still a smooth pale sheet and corrugated
edges; no visual acceptance. Existing SimCache volume-DI warning means no baked
volume replay claim; the readbacks/captures are actual live GPU results.

Seventeen focused liquid Python regressions pass, including discrete face-area
reconstruction, signed overlap conservation, dry-support rejection and explicit
noise tolerance. C++ build passes. Extended engine and sustained-run results
must be recorded separately before making broader claims.

## Sixty-second actual-GPU result

`liquid-terrain-driven-boundary-60s`, log
`CaptureLiquidTerrainDrivenBoundary60s.log`: 3600 steps, complete=true,
88.19s diagnostic wall time. At60s:119,678 live particles, zero nonfinite
positions/velocities and zero sampled bed penetration;84 outside the physical
window. Median speed60.370cm/s, mean67.151cm/s. Upstream/centre/downstream
mean X velocities61.446/47.736/70.415cm/s, counts30,806/33,388/20,469.
Downstream motion persists instead of the preceding unforced tests' stall.
All recorded ages retain zero detected terrain penetration.

Maximum independent analysis-bin occupancy1,010, p95=10 across24,234 bins.
The pathological84,109-particle pile-up in the earlier unforced60s test is
absent, but smaller concentration and rising marker count remain. Neither
marker count nor occupied-bin volume is a calibrated fluid-volume measure.
Current evidence does not prove storage convergence or numerical face flux on
the actual GPU. The fixed opacity-one image remains pale and unrealistically
smooth, with rough edge patches; it was inspected and is not accepted.

Next measure actual grid face velocities/pressure and liquid volume, with
cumulative physical-face entry/exit. Check pressure residual and temporal
settling before claiming hydraulic coupling. Prescribed normal flux on outgoing
faces is an intermediate boundary treatment; outgoing pressure/stage coupling
remains unimplemented. Do not mistake improved motion, candidate compilation,
or sparse particle snapshots for full water/scene acceptance.

Final engine suite `engine-liquid-driven-boundary/index.json`:8 clean passes,
zero warnings/failures,15.425s. The transfer test now covers seven transient
variants, including boundary-array completeness, unit velocity scale and the
actual compiled native-face pressure-drive code. Latest C++ build succeeded;
seventeen Python liquid tests pass, including profile-source identity checks.
These are configuration/data regressions, not a substitute for grid flux and
volume measurement.
