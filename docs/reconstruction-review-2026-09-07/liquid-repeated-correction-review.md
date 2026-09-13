# South Fork: repeated correction, interface transport and inlet coincidences

2026-09-11. The previous user-facing turn was status-only (no implementation
progress). This continuation implemented and tested the changes below. **The
full goal remains active. No playable map, native shader, river terrain, water
volume, momentum, or particle identity was modified in this continuation.**
No build/Unreal process was launched. All owned Python jobs are terminal.

## Whole-domain density, not just the old fluid mask

`liquid_density_projection.py` now reports unclipped density, total excess,
excess squared, kernel-weight sums and maxima for every input phase and the
whole grid. Kernel overlap on a solid-labelled grid point is not itself a
particle penetrating the physical bed. The independent exact-bed/path audit
remains separate. Moving density into an old air/solid label cannot hide it.

Input: all 726,900 particles in `liquid-native-unified-transport-600-v4`.
The first correction is the earlier swept-active-v4 result. New report:
`liquid-geometric-density-global-evaluation-v1.json` (session40582, exit0).

| Actual metric | Native input | First correction | Second correction |
| --- | ---: | ---: | ---: |
| Maximum particle density, all cells | 14.77381 | 12.69585 | 10.08621 |
| Maximum density including bed-kernel fraction | 15.25288 | 13.17493 | 10.56528 |
| Whole-grid squared excess sum | 7405.646 | 5347.268 | 3753.778 |
| Maximum particle density on solid-labelled cells | 4.28377 | 6.05419 | 7.80921 |
| Exact coincident pairs | 89 | 89 | 89 |

Overall error falls, but the growing solid-labelled peak is a material failure
of the current fluid-only pressure support. Do not declare density convergence
or keep applying the same method while ignoring this phase. The geometric
mobility still fixes solid grid nodes and does not implement a cut-cell pressure
or full density constraint on partially open bed-kernel support.

## Transport the interface through the same finite particle map

The position correction uses `F(x)=x+delta(x)`, not RK2 physical-time advection.
New `liquid_correction_map.py` inverts that map by damped Newton queries, then
samples the old scalar at the departure location. Rejected queries remain
explicit failures/NaNs, never an apparently successful unchanged scalar. Solid
and exterior labels stay fixed. Fluid/air changes invalidate pressure factors.
Positive Jacobians at sampled points do **not** prove global injectivity.

First interface package:
`tmp/south-fork-liquid-correction-interface-v1-20260911` (session72587, exit0).
All 749,403 selected fluid/air queries valid, residual <=1e-6 cm, all particle
sampled map determinants positive (minimum0.730336). 1,353 air-to-fluid and500
fluid-to-air cells. The original report's25,493 phi/phase inconsistencies are
ALL in fixed/nonupdated layers; a direct selected-mask check finds ZERO owned
inconsistencies. The latest audit now reports the owned count separately.

`liquid_correction_state.py` verifies native-capture hash, parent manifest,
state hash, unchanged particle count/grid/frame, finite arrays and legal phase
labels. The geometry driver has explicit `--state`; it recomputes density RHS
and pressure factors. It rejects blindly reusing a geometric package as a
density-only seed. In particular, old unscaled `target.bin` must not receive
another unintended application of its recorded target scale. The saved second
package contains its own new unscaled target and updated boundary/density/phi.

## Actual second correction and independent saved-field check

Command (workspace-local SciPy requires the existing elevated Python access):

```text
python physics/scripts/solve_liquid_geometric_density.py
 docs/reconstruction-review-2026-09-07/liquid-native-unified-transport-600-v4
 tmp/south-fork-liquid-geometric-density-swept-active-v4-20260911
 --state tmp/south-fork-liquid-correction-interface-v1-20260911
 --output tmp/south-fork-liquid-geometric-density-second-v1-20260911
 --cached --geometric-mobility --relaxation 1.8 --active-set --swept-contact --iterations 12
```

Session77879, exit0: converged in3 geometry iterations (~216s CPU reference).
Pressure unknowns186,434; final contact rows5,275; final full contact KKT
9.36e-13cm and density equation error1.72e-15. All14 algorithm snapshots at
start remained unchanged. This does not advance physical simulation time.

Independent evaluator session40603, exit0:
`liquid-geometric-density-second-evaluation-v1.json`.
Zero unsupported stencils, endpoint bed crossings, complete straight-path bed
crossings, or exterior violations. Serialized equation error3.00464e-8.
Minimum preserved-skin margin -5.78151e-9m, within the unchanged1e-8m geometry
gate;251 raw negative roundoff margins are retained, not reported as exact zero.
Represented volume15143.75m3 before/after; maximum displacement0.500734cells
(the contact correction can slightly exceed the density seed's0.5cell scale).
The independent evaluator now uses the recorded starting CPU state for a
repeated step, rather than accidentally moving the original native particles.

Second inverse-interface package:
`tmp/south-fork-liquid-correction-interface-second-v1-20260911`, session52509,
exit0, all749,403 queries valid. New pressure-fluid count187,105. No sampled
particle map folds (minimum determinant0.644227). Preserved particle volume.
**Interface sampling is still imperfect:** markers outside the scalar increase
123→144→169 over these passes, with second-pass particle scalar RMS change
0.459922cm/max11.6081cm. Exact inverse query convergence does not remove grid
resampling error or prove interface-volume conservation. No surface promotion.

## Coincident-particle lineage and source-selection candidate

`liquid-native-coincident-lineage-v2.json` retains every pair, immutable IDs,
original-seed lookup, velocities, current bed clearance and native birth step.
All89 pairs have the same respective birth step; none consists entirely of
original wet-volume seeds, and88 are more than2.5cm above the bed. Initial
seed positions have zero exact duplicates. Current owners are4/8. A shared
position-only field cannot separate particles already at exactly one point.

Native source graph evidence:
`RaftSimEditorLiquidTerrainSource.cpp` assigns `Particles.RiverSourceIndex`
using `SelectIntFromWeightedDistributionArray`; position and velocity read the
selected array entry. `RaftSimLiquidRegionalState.cpp` supplies the same discrete
weighted source arrays. Independent with-replacement draws can pick one point
twice within a birth batch. This is a strong, actionable cause candidate, **not
yet an independently captured birth-site proof**. Do not silently merge/jitter
existing coincident water to conceal it.

`liquid_stratified_source.py` supplies a tested CPU candidate: one shared uniform
offset per native spawn batch, quantiles `(i+u)/N`, weighted CDF lookup. Spawn
counts, source positions/velocities, weights and volume remain unchanged. Each
site's expected count is N*p; counts differ from that expectation by less than
one. A genuinely high-weight site may still receive multiple births; no cap
or source-water deletion is permitted.

`liquid-stratified-source-reference-v2.json` checks the actual600-step capture
(the journal also includes2 later observed steps, explicitly excluded). All
599 subsequent birth batches per emitting owner are represented through their
distinct counts: owner4=32/33, owner7=1/2, owner8=4/5. 256 offsets per distinct
count, including float32 CDF/quantile emulation: zero duplicate site selections,
zero positive weights collapsed to zero. Largest N*p is0.0119142 (<1).
**Not installed in native Niagara yet.**

Local UE5.8 shader evidence for integration: in
`NiagaraEmitterInstanceShader.usf`, `SetupExecIndexAndSpawnInfoForGPU` makes
`ExecIndex()` relative to the individual SpawnInfo group and sets
`Engine_ExecutionCount` to that group's count (lines162–198). Do not use total
live particles as the stratum count, or independently randomize u per particle.
Keep original initial-volume burst untouched and verify groups/IDs on GPU.

## Verification and next work

489 liquid unit/regression tests PASS (full discovery, elevated local SciPy).
New regressions cover hidden air/solid clumps, kernel accounting, finite-map
inverse, folded/unsupported queries, phase invalidation, tampered/wrong state,
exact duplicate grouping and weighted stratification including dominant sites.
Map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No native/visual/FPS acceptance, map promotion, final commit or push.

Next available concrete work:

1. Capture native birth source indices/group counts and install/verify the
   stratified source selector on the transient regional path. Keep burst,
   rates, volume, site velocity and physics clocks unchanged; verify actual
   new births and extended native flow, not only CPU sample counts.
2. Resolve the growing partially-solid kernel concentration with physically
   consistent bed/pressure/density support; do not move terrain or remove mass.
3. Correct scalar resampling/interface-volume drift; repeated projection is
   not yet a complete consistent water state, much less physical-time flow.
4. Native feasible correction/pressure/interface coupling, long-run storage
   and discharge, one rendered surface/foam/spray, raft response and playable
   performance, then all remaining scenes/crew/cleanup/release/commit in the
   original goal order. CPU seconds above are NOT playable FPS measurements.
