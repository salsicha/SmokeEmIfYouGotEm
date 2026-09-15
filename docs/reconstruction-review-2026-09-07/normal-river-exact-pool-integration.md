# Exact source geometry through wet-pool state

September 14, 2026. **Research pool integration completed; qualified finite-time
physics, native water, visual realism and 30 FPS remain incomplete.**

## The retained representation now reaches evolving pool candidates

`SubcellGeometryPatch(..., relative_stages=True, exact_sources=True)` selects
original rational source fragments and source-relative storage instead of
reconstructing storage from rounded triangle vertices. The default remains
unchanged. The actual-source audit exposes the option as `--exact-pool-geometry`.

The existing wet-pool machinery now preserves that representation through:

- Initial separated-pool construction and original-source storage subsets.
- Exact physical datums in pool forms, distinct from local numerical zero.
- Exact Cartesian face traces, their intersections and independent ownership
  checks on an exact knot sweep.
- Original internal source edges and their endpoint elevations. The projected
  length and unit normal remain numerical values derived from the original
  edge; no displacement or forced common pool stage is introduced.
- Original two-pole pressure, analytic directions and inverse-metric energy.
- Volume probes, source-topology intervals, wet-support release/splitting,
  source-front activation and returned candidate state.

Topology boundaries use retained source elevations rather than rounded global
levels. A source trace with no positive overlap is not connected. Conflicting
owners are rejected rather than unioned or welded. Physical height differences
are formed in the source frame before numerical conversion. The conservation,
energy, represented-range and original 40-iteration pressure gates remain.

The new path is not merely a separate geometry report: its actual pressure and
history runs use these storage objects, forms and traces throughout. It is
still explicitly selected research code, not the playable/native solver and
not the complete rational nonlinear dynamics.

## Compatibility failures reproduced and corrected

New tests first found an old aggregate energy helper treating local numerical
zero as global elevation. On the translated ramp control, potential energy was
10.066858 instead of 11.501571. It now uses the same exact physical reference
datum as pool energy; no energy is adjusted after calculation.

Other old aggregate-rate entry points could bypass pool-aware geometry and
misread those local datums. Exact-source patches now reject the legacy direct,
paired aggregate and frozen-aggregate evolution paths. They must use the
pool-aware state/flux path. Ordinary legacy callers are not switched.

Seven new integration tests cover separated pools, both pressure poles against
an independent dense solve, source subdivision/internal edges, volume probes,
activation into a dry source region, returned-state provenance, energy frame
agreement and the aggregate bypass guards. No existing failing test is removed
or relabeled as passing.

## First actual integrated history: geometry gap removed, dynamics still fail

The first actual run uses the same original 600-second atlas and captured /
inferred source mesh. All 258 initial pools retain their source frames. Both
original pressure poles pass in 40 iterations, including the independent dense
solution check. The requested history remains 20 fixed steps of 20 ms.

Every attempt now reports zero source faces below its owning storage minimum.
That discrepancy is removed by using the same source geometry, not by clamping
a face, moving terrain, imposing a depth floor or relaxing its comparison.

Seventeen candidates reach 0.34 seconds and 420 regions, then step 18 rejects
four zero solved volumes. Three of those regions have incoming transfer. This
is not a set of isolated drains that can simply be deleted at a threshold.

There is also a local speed warning at step 17: parent 141 / source 200252
reaches 8.67694 m/s with volume 7.90168e-256. Its old volume is 4.85448e-195.
The direct remainder is approximately (4.51914e-192, -6.75740e-192), dominated
by pressure, with no negative-exchange or dry-front contribution. The global
base and full energies decrease, but that does not qualify the local dynamics.
Conservative drying, coupled inflow and pressure/force timing remain required.

## Final actual and regression verification

Final run completed with exit 1, preserving the unmet history/transport gates:

```powershell
python -B physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/south-fork-exact-pool-integrated-v2-20260914.json --exact-pool-geometry --pool-direction --pool-transport --pool-history-steps 20 --pool-history-scheme coupled-donor
```

Report SHA256:
`c0d4954f3a0ec5bb8e7b12b906a0b1e064a0b1713330cf3aaa0c5bc05da31734`.
All 40 recorded source hashes match the final implementation and data.
Exact in-memory datums remain rational; JSON elevation and trace fields are
explicitly identified as float projections, backed by original source hashes.

The 258-pool original-pole static pressure and analytic direction controls
pass. Independent direction-probe errors remain below the existing 1e-6 gate;
the largest reported energy/momentum-direction error is 1.8538e-8. The physical
energy controls also pass: original-pole momentum round-trip error per volume
is 1.27494e-10, dense canonical-velocity error is 7.66054e-15, and forward/reverse
volume-work discrepancy is 1.83575e-15. Original kinetic/potential/total energy
is 2156.913766390772 / 9369.056889819043 / 11525.970656209814.

The fixed-topology transport report still has 57 unowned-source wet trace
entries across 18 parents. It does not expose partial assembled rates as
complete evolution. The separately attempted one-sided activation path is
subject to its original finite-state and full-energy rejection checks.

The entire final history is identical to the first integrated run described
above. Maximum per-step mass and momentum-balance errors are 1.13687e-13 and
1.30562e-12 over the 17 candidate steps. They do not waive the speed warning,
four zero solved volumes or missing conservative drying closure. The first
report is `tmp/south-fork-exact-pool-history-v1-20260914.json`, SHA256
`63263a3f07f86262ba3ae295d202add70c6a2982140d4973ed12540c124f7987`.

Final focused tests: **218 passed, 1 failed**; XML time 14.813 seconds.
`tmp/subcell-exact-pool-tests-v2-20260914.xml`.
Retained original energy selection: **25 passed, 12 failed**; XML time 7.316
seconds. `tmp/subcell-exact-pool-retained-v1-20260914.xml`.
All 464 protected source/capture/map/profile/actor hashes remain unchanged.
Generated reports stay ignored local evidence; no external media is downloaded.

## Remaining scope

The original old float-storage/face equality regression still fails; the new
path is not used to waive that gate. Original nonlinear and legacy energy
failures also remain. Full rational transport/pressure/bed-force coupling,
physical wet-front events, time/open/refinement checks and native shared-surface
integration are still required before this becomes playable water.

No native code, scene map, menu, captured terrain, water atlas, render quality
or performance setting is changed. This is not a visual or FPS gain. South Fork
precedes Colorado, Pacuare and Futaleufu; Chilko/Zambezi reviews, crew realism,
fit/animation, normalization, regressions and release checks remain open.
Troublemaker remains a rapid within South Fork, not a standalone menu scenario.
The full goal remains active.
