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

- PID: **36692**; start UTC: **2026-09-23T18:34:26.9266900Z**.
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
**1000 / 15050 s**. Run
both `audit_cartesian_cook_snapshot.py` and `audit_cartesian_exterior_banks.py`
on that checkpoint, then reassess later regional storage trends. Do not launch
a duplicate while this run is live or treat buffered progress output as a stall.

## Unchanged acceptance limits

Captured data, normal playable geometry/collision and installed 4950 s fields
remain unchanged. Native nonlinear mode remains OFF. This run delivers no
new visible detail, rebuilt game, motion, collision or performance acceptance.
The short normal-start publication-cache tests do not supersede the unresolved
rapid-workload performance failure or whole-river validation. The rock-cap
interpretation decision remains pending; no unsupported source relabeling or
rejected canopy retuning was performed. South Fork remains unfinished, ahead
of Colorado, Pacuare and Futaleufu.
