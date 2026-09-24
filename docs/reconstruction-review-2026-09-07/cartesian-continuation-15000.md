# South Fork exact continuation from 15000 seconds

## New completed checkpoint:16900s (September24)

Original cook36692 was verified live with its original creation time; no new
cook was launched. Complete local38000/16900s passes both independent snapshot
and exterior-bank audits. All5,382,400 h/u/v cells are finite; maximum depth
3.256262318m, maximum speed4.851050237m/s. All86,720 artificial-bank cells remain
exactly dry. Volume2067671.046570m³ differs from the native driver by only
−1.629815e−9m³; maximum per-step conservation residual remains9.483589469e−9m³.
Depth SHA256 `c49fc9c4206311d9ae0c17d824f99f4cfdb2fa7d226e7a8382120c54168c1719`.
Reports: `tmp/cartesian-16900-state-v1-20260924.json` and
`tmp/cartesian-16900-banks-v1-20260924.json`.

Instantaneous outlet103.142577m³/s still exceeds inlet45.306955m³/s: **not
settled**, not eligible for promotion. New regional comparisons use the same
unchanged route partition, physical inputs and integrated conservation checks:

| Model-time interval | Station0–9km | Station9–26km | Station26km–end | Domain |
| --- | ---: | ---: | ---: | ---: |
|16550–16750s|−0.001218|−27.812563|−32.544693|−60.358475m³/s|
|16750–16900s|−0.001305|−26.308281|−32.418417|−58.728003m³/s|

These are storage-change rates, not numerical cross-section fluxes. Integrated
exterior closure errors are−8.00e−11 and1.22e−10m³. The middle/lower reach still
drains; tiny upper-reach net storage alone does not prove local equilibrium or
justify partial field promotion. Report:
`tmp/cartesian-storage-regions-16900-v1-20260924.json`. Skipped checkpoints are
not implicitly state/bank-audited. Next selected complete snapshot must be newer
than16900s. No settling-time forecast, bathymetry/outlet calibration acceptance,
new playable geometry, build, motion or performance acceptance follows here.
Normal installed4950s fields and nonlinear OFF remain unchanged.

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

Local10000/15500 and11000/15550 s now pass both audits. All5,382,400 cells
are finite and all86,720 artificial-bank cells remain exactly dry. Latest
maximum depth3.487468730 m, speed4.970119220 m/s, volume2153817.610698 m³
(−38459.857464 m³ from restart), maximum per-step residual9.483589469e−9 m³.
Combined outflow117.241668 at15500 s and112.947736 m³/s at15550 s still exceeds
inflow45.306955 m³/s: NOT settled. Reports are
`tmp/cartesian-15500-state-v1-20260923.json`,
`tmp/cartesian-15500-banks-v1-20260923.json`,
`tmp/cartesian-15550-state-v1-20260923.json` and
`tmp/cartesian-15550-banks-v1-20260923.json`, bound in the
[filtering follow-through receipt](water-shadow-filter-review.json).
The same original cook is the sole live engine/cook job; no fields promoted.

Local12000/15600,13000/15650 and14000/15700 s now pass both independent
audits. All5,382,400 cells remain finite and all86,720 artificial-bank cells
remain exactly dry. At15700 s maximum depth is3.459829193 m and maximum
speed4.956530141 m/s. Volume2143575.428078 m³ is48702.040084 m³ below restart;
maximum per-step conservation residual remains9.483589469e−9 m³.
Combined instantaneous outlet111.894383 m³/s exceeds inlet45.306955 m³/s.
This does NOT establish settling. Reports:
`tmp/cartesian-{15600,15650,15700}-{state,banks}-v1-20260923.json`.
Latest depth SHA256:
`fda368b043167d53d62de0ede0e7056de328a2c24ddcdf5a180e043499ccb05e`.
The six audit invocations completed successfully; no engine job, duplicate cook,
source mutation or field promotion was performed.

Next complete local15000/15750 s needs both `audit_cartesian_cook_snapshot.py`
and `audit_cartesian_exterior_banks.py`. Do not launch a duplicate while this
run is live or treat buffered progress output as a stall.

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

## Regional storage through15700 s

A new read-only report extends the same partition and hash checks to completed
local6000/15300,10000/15500 and14000/15700 s snapshots. These are equal200 s
intervals, distinct from the earlier150 s intervals. Storage rates are not
cross-section discharges or measured river observations.

| Model-time interval | Station0–9 km | Station9–26 km | Station26 km–end | Domain |
| --- | ---: | ---: | ---: | ---: |
|15300–15500 s|−0.00437|−39.96950|−29.48141|−69.45528 m³/s|
|15500–15700 s|−0.00356|−37.85834|−30.55175|−68.41364 m³/s|
|15300–15700 s|−0.00396|−38.91392|−30.01658|−68.93446 m³/s|

Regional sums agree with integrated exterior volume to within2.73e−10 m³.
Middle-reach storage loss eases while downstream loss grows; distributed
drainage remains substantial. The upper-region aggregate alone does not
qualify individual rapid stages, local velocities, terrain alignment or a
partial field promotion. Do not extrapolate an equilibrium time from these
intervals or tune outlet stage to force balance.

Report: `tmp/cartesian-storage-regions-15700-v1-20260923.json`, SHA256
`2f4f8ccac62eb8d5bcc4db0c63913d983286c29324a03ffe3c7d97326564c64e`.
Session26678 is terminal exit0. This is supporting hydraulic qualification,
not visible delivery; the same cook continues with unchanged inputs.

## New completed checkpoint at16150 s

Local23000/16150 s now passes both independent state and exterior-bank audits.
All5,382,400 h/u/v cells are finite; maximum depth3.379908945m, speed4.919573249m/s,
maximum per-step conservation residual9.483589469e-9m³. All86,720 artificial-bank
cells remain exactly dry. Volume2113743.264080m³ is down78534.204083m³ from restart.
Combined instantaneous outflow108.828006m³/s still exceeds inflow45.306955m³/s;
this is NOT settled and must not be installed into normal gameplay.
Reports `tmp/cartesian-16150-state-v1-20260923.json` and
`tmp/cartesian-16150-banks-v1-20260923.json` are terminal exit0 in session21157.
Depth SHA256 `cd216cae2171798a0301c06811ceaef1ea625dfff9afab7a094150405f8c217e`.
This jumps forward to a newly completed state; intervening unaudited checkpoints
are not implicitly marked passed. The original identified cook36692 continues;
no duplicate cook, input adjustment, source relabeling or field promotion.

## Unchanged acceptance limits

### Heartbeat qualification at16400 s

The newly completed local28000/16400 s checkpoint passes both read-only audits
in a terminal exit0 invocation. All5,382,400 h/u/v cells are finite; maximum
depth3.337946646m, speed4.893295846m/s and per-step residual9.483589469e-9m³.
All86,720 artificial-bank cells remain exactly dry. Snapshot volume agrees
exactly with the driver:2097839.068451m³, down94438.399712m³ from restart.
Combined outlet108.317588m³/s still exceeds inlet45.306955m³/s: NOT settled.

Fresh reports: `tmp/cartesian-16400-state-heartbeat-20260923.json` and
`tmp/cartesian-16400-banks-heartbeat-20260923.json`. Depth SHA256:
`d23f62f1490980fe1b3eb865a726d01d84f4eee477fc3090dca1be240ca6139a`.
Intervening checkpoints are not implicitly qualified. Live-work checks found
the existing project task active and the original cook36692 as the sole
engine/cook process. No competing editor/build/cook or runtime edit was started.
This is new checkpoint qualification only, not a delivered playable change;
normal-scene motion, collision, shoreline, surface and performance acceptance
remain open. Continue playable work without promoting this unsettled state.

### Heartbeat qualification at16550 s

The new complete local31000/16550 s state passes both independent read-only
audits (terminal exit0). All5,382,400 h/u/v cells are finite; maximum depth
3.312954579m and speed4.882631273m/s. All86,720 artificial-bank cells remain
exactly dry. Volume2088551.941968m³ is103725.526194m³ below restart; driver
agreement is within1.40e-9m³ and maximum per-step residual9.483589469e-9m³.
Instantaneous outlet108.915050m³/s versus inlet45.306955m³/s remains unsettled.
Fresh reports are `tmp/cartesian-16550-state-heartbeat-20260923.json` and
`tmp/cartesian-16550-banks-heartbeat-20260923.json`; depth SHA256:
`9d398f87dfd401e0ddbdeb45681c3e3b4006bd49dff04448a39fb8db889303ea`.

A new regional audit compares16150,16350 and16550 s using the same unchanged
nearest-route-sample partition, input hashes and integrated-boundary checks.
It completes exit0 (session9145). These are storage rates, not section fluxes:

| Model-time interval | Station0–9 km | Station9–26 km | Station26 km–end | Domain |
| --- | ---: | ---: | ---: | ---: |
|16150–16350 s|−0.00185|−31.44165|−32.37702|−63.82052 m³/s|
|16350–16550 s|−0.00140|−29.59531|−32.53938|−62.13610 m³/s|

Regional sums close against integrated exterior volume within3.57e-10m³.
Middle-reach loss eases, but lower-reach loss still increases slightly and
domain drainage remains substantial. This does not qualify local rapid
stages or justify partial promotion, outlet tuning or a settling-time forecast.
Report: `tmp/cartesian-storage-regions-16550-heartbeat-20260923.json`, SHA256
`9ff9e06caf4e68530defcaa0bd57830929b92120bcbadb20ccb04d5343d66796`.

The identified original cook36692 remains the only engine/cook process; no
duplicate was launched. The active task in the inventory is this calling task,
not evidence of another worker. This increment qualifies new completed data,
not an unchanged failed trial. It delivers no playable or build change. The
next checkpoint selected for qualification must be newer than16550 s and have
its complete marker; intervening states are not implicitly passed. Continue
normal-play improvements independently without installing unsettled fields.

Captured data, normal playable geometry/collision and installed 4950 s fields
remain unchanged. Native nonlinear mode remains OFF. This run delivers no
new visible detail, rebuilt game, motion, collision or performance acceptance.
The short normal-start publication-cache tests do not supersede the unresolved
rapid-workload performance failure or whole-river validation. The rock-cap
interpretation decision remains pending; no unsupported source relabeling or
rejected canopy retuning was performed. South Fork remains unfinished, ahead
of Colorado, Pacuare and Futaleufu.
