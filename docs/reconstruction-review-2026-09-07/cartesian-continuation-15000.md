# South Fork exact continuation from 15000 seconds

Reviewed 2026-09-23 UTC. Supporting hydraulic work only; no playable promotion.

The preceding 12000–15000 s cook is terminal. Its final state and dry-bank
audits pass, but combined instantaneous outflow is 115.020881 m³/s against
45.306955 m³/s inflow. It is not settled. The retained
[regional storage accounting](affine-source-pullback-and-15000-review.md)
shows middle-reach drainage decreasing while downstream storage changes from
accumulation to drainage. This warrants further exact-state evolution, not
altering the outlet to force an instantaneous discharge match. It does not
prove the inferred bathymetry or outlet calibration correct.

## Restart qualification

The prepared input already existed when this heartbeat resumed. Its manifest
was complete and no preparer, cook or engine process remained live. It was
reused without regenerating or overwriting it. After checking the executable
and input hashes, a fresh output path and 34.5 GB free disk, one bounded native
continuation was launched.

The [independent native restart audit](cartesian-restart-15000-audit.json)
checks all **5,382,400** retained depth/u/v cells bit-for-bit against the final
15000 s snapshot. Grid, bed, roughness, boundaries, features, probes and all
retained physical settings are unchanged. No cells or water were added.
The volume summation difference is −1.3969838619232178e−9 m³; no correction
was applied. Source and native initial clocks both equal
14999.999999921967 s. All 51 focused restart-metadata, retained-input and
regional-storage tests pass.

## Live identity and next checkpoint

- PID: **36692**; exact .NET start UTC: **2026-09-23T18:34:26.9266904Z**.
  CIM reports microsecond precision (`...9266900Z`); use the .NET value above
  with the profiling helper's exact retained-handle identity guard.
- Tool session: **68019**. Check the complete process identity before treating
  this PID as live or pausing it for engine profiling.
- Executable: `tmp/solver-worker-limit-v1-20260917/raftsim_cartesian_cook.exe`.
- Executable SHA256: `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
- Input: `tmp/control-ablation-15000to18000s-input-v1-20260923/manifest.json`.
- Input SHA256: `d84f17873ca39f42f59ba069aaea102e8439024434445063b31a3f9c5e1f6e65`.
- Output: `tmp/control-ablation-15000to18000s-workers8-v1-20260923`.
- Restart audit SHA256: `c8bbf6cc5656a212b9f2243f690f28bc77b5e767635ede41c91e65777c3e2d07`.

Unchanged settings: dt 0.05 s, eight worker lanes, 60,000 steps and snapshots
every 1,000 steps (50 model seconds). The target is 18000 s, not a prediction
of settling time. Native frame zero is complete; observed progress reaches
local230 / 15011.4999999218 s with maximum per-step conservation residual
8.7392675318653801e−9 m³. The first new complete checkpoint is local
**1000 / 15050 s**, now independently audited: all5,382,400 cells are finite,
maximum depth3.579930135 m, speed5.034237693 m/s, maximum step conservation
residual9.483589469e−9 m³. All86,720 artificial-bank cells remain exactly dry.
Volume falls3540.635963 m³ in50 s; instantaneous combined outlet117.517386 m³/s
still exceeds inlet45.306955 m³/s. This is not settled. Retained reports:
`tmp/cartesian-15050-state-v1-20260923.json` and
`tmp/cartesian-15050-banks-v1-20260923.json`.
The next checkpoint, local2000/15100 s, also passes both audits: maximum
depth3.570577408 m, speed5.027625187 m/s, maximum step conservation residual
9.483589469e−9 m³. All86,720 artificial-bank cells remain exactly dry.
Volume is2185204.713700 m³, down7072.754462 m³ from the restart. Combined
instantaneous outlet115.512228 m³/s still exceeds inlet45.306955 m³/s.
Retained reports: `tmp/cartesian-15100-state-v1-20260923.json` and
`tmp/cartesian-15100-banks-v1-20260923.json`. This is not settling acceptance.
Local3000/15150 s now also passes both audits. All5,382,400 cells remain finite;
maximum depth3.561168726 m, speed5.020982768 m/s, maximum step conservation
residual9.483589469e−9 m³. All86,720 artificial-bank cells remain exactly dry.
Volume is2181676.392980 m³, down10601.075183 m³ from restart; combined outlet
115.279190 m³/s still exceeds inlet45.306955 m³/s. Snapshot/driver volume
disagreement is1.396983862e−9 m³. Reports:
`tmp/cartesian-15150-state-v1-20260923.json` and
`tmp/cartesian-15150-banks-v1-20260923.json`.
The depth-array SHA256 is
`b2d14fb0bf60697ef60649e40d6a0324b7ff3e67d35efd16bc3e3cb534eebada`.
Live process identity was rechecked unchanged after the audit; CPU time advances.
This checkpoint is a verified continuation, not a settling or playable gain.

Local4000/15200 s also passes both audits (reports
`tmp/cartesian-15200-state-v1-20260923.json` and
`tmp/cartesian-15200-banks-v1-20260923.json`). The subsequent completed
local5000/15250 s checkpoint passes both independent audits: all5,382,400
cells remain finite, maximum depth3.542773217 m and speed5.007881615 m/s.
All86,720 artificial-bank cells remain exactly dry; maximum per-step residual
is9.483589469e−9 m³. Volume is2174648.258995 m³, down17629.209168 m³
from restart. Combined instantaneous outlet112.689760 m³/s still exceeds
inlet45.306955 m³/s, so this is NOT settling acceptance. Reports:
`tmp/cartesian-15250-state-v1-20260923.json` and
`tmp/cartesian-15250-banks-v1-20260923.json`. Depth-array SHA256:
`ad3ef622c95e3776b0bbcf7b9a58656447677017b89cdf31c331baad79ab2c6f`.
The original cook36692 remains live; it does not use the separate solver-stage
storage optimization currently being integrated into the normal game build.
No duplicate cook was launched and no fields were promoted.

Local6000/15300 s subsequently passes both audits. All5,382,400 cells are finite;
maximum depth3.533532067 m, speed4.997859218 m/s, maximum per-step residual
9.483589469e−9 m³. All86,720 artificial-bank cells remain exactly dry.
Volume2171149.212900 m³ is21128.255262 m³ below restart, with snapshot/driver
volume disagreement9.313225746e−10 m³. Combined outlet115.981630 m³/s exceeds
inlet45.306955 m³/s: still unsettled, with no monotonic-outlet claim. Reports:
`tmp/cartesian-15300-state-v1-20260923.json` and
`tmp/cartesian-15300-banks-v1-20260923.json`. Depth-array SHA256:
`530bc9de310610e156ab388a0343e09ae2d62e78f64986e0f12e9555264364c4`.

Local7000/15350,8000/15400 and9000/15450 s now pass both independent audits.
All5,382,400 cells remain finite and all86,720 artificial-bank cells exactly dry.
At15450 s maximum depth is3.505866495 m, speed4.979140831 m/s, volume
2160712.893493 m³ (31564.574669 m³ below restart), maximum per-step residual
9.483589469e−9 m³. Outlet113.721042 still exceeds inlet45.306955 m³/s.
This is not settled; no fields are promoted. Reports follow the existing pattern
`tmp/cartesian-{15350,15400,15450}-{state,banks}-v1-20260923.json`.
Latest depth SHA256:
`91395922ee38a462bd0604f629e15a945028e39e0e2d13242c2911b322bf6ebd`.
The same original cook remains live without a duplicate or input change.

Next complete local10000/15500 s needs both `audit_cartesian_cook_snapshot.py`
and `audit_cartesian_exterior_banks.py`, then reassess later regional storage trends. Do not launch
a duplicate while this run is live or treat buffered progress output as a stall.

## Regional storage through15300 s

The unchanged read-only regional audit now compares restart,15150 s and15300 s.
All5,382,400 cells are partitioned using the same nearest-route-sample station
bands as the retained15000 s review; input scenarios, beds, route and complete
snapshot identities are checked. These are storage rates, NOT section discharges.

| Model-time interval | Station0–9 km | Station9–26 km | Station26 km–end | Domain |
| --- | ---: | ---: | ---: | ---: |
|15000–15150 s|−0.00538|−43.52063|−27.14782|−70.67383 m³/s|
|15150–15300 s|−0.00487|−41.86152|−28.31481|−70.18120 m³/s|
|15000–15300 s|−0.00512|−42.69108|−27.73132|−70.42752 m³/s|

Regional sums match integrated exterior volume to within2.73e−11 m³.
Middle-reach loss eases while downstream loss grows over these two150 s
intervals. This extends the earlier distributed-transient observation; it
does not establish the cause, validate bathymetry/outlet stage or predict a
settling time. Continue the existing unmodified cook; do not tune the outlet
to force instantaneous balance or promote these states into gameplay.
Report: `tmp/cartesian-storage-regions-15300-v1-20260923.json`, SHA256
`8c52a34613af2095205da13111cbc27fc595ed802a6959d3470489d0529c1474`.
The audit is terminal exit0; no additional cook was launched.

## Unchanged acceptance limits

Captured data, normal playable geometry/collision and installed 4950 s fields
remain unchanged. Native nonlinear mode remains OFF. This run delivers no
new visible detail, rebuilt game, motion, collision or performance acceptance.
The short normal-start publication-cache tests do not supersede the unresolved
rapid-workload performance failure or whole-river validation. The rock-cap
interpretation decision remains pending; no unsupported source relabeling or
rejected canopy retuning was performed. South Fork remains unfinished, ahead
of Colorado, Pacuare and Futaleufu.
