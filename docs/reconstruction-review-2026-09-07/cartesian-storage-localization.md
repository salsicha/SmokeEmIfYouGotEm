# South Fork: where the continuing hydraulic imbalance is stored

This is supporting diagnosis, not a visible playable change or river acceptance.
No map, terrain, collision, installed 4950 s fields, boundary forcing, or solver
configuration changed. The nonlinear solver stays off. The cap interpretation
decision remains pending; later rivers remain queued.

## New finding

The roughly 59 m³/s continuing volume loss is **not localized at the outlet**.
Between simulation times 11500 and 11950 s, the middle reach loses storage while
the downstream reach gains it. Thus an outlet-only drainage explanation is
inconsistent with these snapshots. The result is compatible with a distributed
transient moving through the long reach, but does not establish its physical
cause or calibrate the inferred bed/outlet stage.

Storage-change rates below include every cell, not just wet cells. Negative is
loss; positive is accumulation. These are NOT section discharge measurements or
independently sampled numerical face fluxes.

| Time interval (s) | Station 0–9 km | Station 9–26 km | Station 26 km–end | Whole domain |
|---|---:|---:|---:|---:|
| 9000–11000 | −0.01 | −63.85 | +5.29 | −58.57 m³/s |
| 11000–11500 | −0.01 | −72.45 | +13.33 | −59.13 m³/s |
| 11500–11950 | −0.01 | −73.15 | +14.12 | −59.03 m³/s |

In the last interval the median common-wet stage falls 7.15 cm in station band
18–19 km, but rises 4.41 cm in band 29–30 km. Even when net domain loss barely
changes, the internal redistribution is substantial. The first 9 km being
relatively stable does not make the whole reach settled or validate its shape.

Actual wet boundary-cell median stages stay close to the authored outlet stage
of −88.958572 m relative to the 220 m datum. At 11950 s, the two west outlet
edges have medians −88.956560 and −88.958040 m (45 and 56 wet cells). These are
interior-cell samples, not ghost stages; proximity to an imposed stage is not
evidence that that stage is physically correct. Endpoint probe snapshots are
not substituted for time-integrated flux.

## Reproducible checks

The new `physics/scripts/audit_cartesian_storage_regions.py` operates only on
completed snapshots of the existing cook. It verifies copied/original manifest
identity, scenario and static-bed hashes, unique tile ownership, complete
markers, depth layout/finiteness/nonnegativity, clock/step agreement, and native
volume agreement. Each of the 5,382,400 cells belongs to exactly one nearest
route-sample 1 km station band in native east/north coordinates. The grid origin
is the first cell center, matching native solver diagnostics; no half-cell
offset or world-Y reflection is applied. Endpoint
context is assigned to its endpoint band. These are attribution regions, not
surveyed river cross-sections; nearby bends can affect the nearest assignment.

All regional storage changes sum back to the full-domain change and the native
time-integrated exterior boundary volume. Largest absolute closure discrepancy
over the four reported comparisons is below 2.1e−9 m³. The full 9000–11950 s
change is −173271.619700 m³. This verifies accounting, not equilibrium.

Retained [machine-readable evidence](cartesian-storage-regions-11950.json)
contains all bands, largest-loss tiles, boundary-cell stage samples, complete
frame records and depth/manifest/route hashes. Source arrays remain in ignored
`tmp/control-ablation-9000to12000s-workers8-v1-20260918`; no raw captures are
copied into Git. Run from the repository root with the project's NumPy/SciPy
environment:

```powershell
python physics/scripts/audit_cartesian_storage_regions.py `
  tmp/control-ablation-9000to12000s-workers8-v1-20260918 `
  physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/coordinate_map.json `
  --steps 0 40000 50000 59000 --report tmp/FRESH-storage-report.json
```

Seventeen focused tests pass: native coordinate orientation/first-cell center, complete partition,
wetting/drying, empty bands, closure, duplicate ownership, invalid depths/time,
and rejection of corrupted manifest, bed, volume, flux, marker and clock.
Full-state/artificial-bank audits also pass separately at local 48000 through
59000 (simulation 11400 through 11950 s), with all artificial banks exactly dry.
Reports are retained under `tmp/vest-followup-baseline-*` through 58000 and
`tmp/storage-followup-baseline-59000-*`. None constitutes settling acceptance.

## Consequence for the next step

Do not tune the outlet stage merely to make the instantaneous output equal the
inlet, and do not launch a duplicate or fresh-initialized cook. The sole existing
process is PID 13584, started 2026-09-18T12:17:39.4321093Z, continuing 9000→12000 s.
At this review it is still advancing. Next unaudited checkpoint is the terminal
local 60000 / 12000 s; confirm its marker and process outcome, then perform both
existing audits. A continuation decision must retain this spatial accounting
and inspect the middle/downstream stage trend, rather than rely on finite
arrays or instantaneous outlet probes alone. The present data do not estimate
a trustworthy remaining settling time or justify promotion to the game.

No new build, gameplay capture, motion, collision or FPS acceptance is claimed.
The last measured default-game result remains 25.003520 FPS / p95 48.329 ms,
below the user's 30 FPS target.
