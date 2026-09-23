# South Fork exact continuation at 12000 seconds

Reviewed 2026-09-19 UTC. Supporting hydraulic work only; no playable promotion.

Update2026-09-23: the continuation described below is now terminal at15000 s.
Both final audits pass, but the reach remains unsettled and downstream storage
is now falling. See [final state and regional accounting](affine-source-pullback-and-15000-review.md).
Do not reuse PID12672 in profiling or restart its already completed cook.

The preceding 9000→12000 s cook (PID 13584) is terminal: its process is absent,
its native `completed.json` records completion, and local frame 60000 is complete.
An OS exit-code receipt was not recovered; native completion and independently
validated final arrays are the evidence, not a claimed observed exit code.

Both full-state and artificial-bank audits pass at the final checkpoint:

- Time: 11999.999999965623 s; volume: 2391074.3804893242 m³.
- Maximum depth: 4.0047184566090861 m; maximum speed: 5.399105405679367 m/s.
- Maximum per-step conservation residual: 1.4294283534610486e−8 m³.
- All 86,720 artificial-bank sample cells remain exactly dry.
- Instantaneous combined outlet flow: 102.71483374432633 m³/s versus
  45.30695454719997 m³/s inlet. These instantaneous values do not replace the
  time-integrated volume accounting. The reach is **not settled**.

The final audit artifacts are preserved in ignored tmp:

| Artifact | SHA256 |
|---|---|
| `storage-terminal-12000-state-v1-20260918.json` | `1ff681283108f52e51d91e993ce13db2f96bebb2b57335a8f88018e0af79901c` |
| `storage-terminal-12000-banks-v1-20260918.json` | `149486b9851b11cd2b090920e3458fa9e6d94e64c08cd8b8724b30d9388b8d03` |

## Why continue this state

The [full-reach storage audit](cartesian-storage-localization.md) changes the
next action: the middle reach is draining while the downstream reach is still
accumulating water, with almost no upstream storage change. This is consistent
with a distributed transient and does not support adjusting only the outlet to
force discharge equality. It does not identify the cause or prove the inferred
geometry/outlet calibration correct. Continue the same state, with regional
stage/storage trends retained for reassessment; do not reset initialization or
promote an unsettled checkpoint.

## Exact native restart and live identity

The prepared continuation has no added cells or water. Its independently
loaded native frame zero matches all **5,382,400** preceding depth/u/v cells
bit-for-bit. Grid, bed, roughness, boundaries, features, probes and every retained
physical setting are unchanged. The observed volume summation difference is
−1.862645149230957e−9 m³; no volume correction was applied.

[Independent restart audit](cartesian-restart-12000-audit.json).
All 51 focused restart-metadata, retained-input and spatial-storage tests pass.

Only one cook was launched, after confirming there was no live cook and more
than 11 GiB of free disk reserve. The bounded continuation retains dt 0.05 s,
eight workers, 60,000 steps and snapshots every 1,000 steps (50 model seconds).
It targets 15000 s; this is not a settling-time prediction. Output is fresh and
the old run/source arrays remain intact.

- PID: **12672**; start UTC: **2026-09-19T00:22:58.0823059Z**.
- Tool session: **79088**. Process identity, not an observation timeout, decides
  whether it is still live.
- Executable: `tmp/solver-worker-limit-v1-20260917/raftsim_cartesian_cook.exe`.
- Executable SHA256: `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
- Input: `tmp/control-ablation-12000to15000s-input-v1-20260918/manifest.json`.
- Input SHA256: `35bd312ff766d8985f2e9d852a7b1a1123a4e8f74f69846cd15aa696d8a90815`.
- Output: `tmp/control-ablation-12000to15000s-workers8-v1-20260918`.

Direct process inventory confirms it is the sole cook. CPU time advances from
234.203125 to about 884 s; progress reaches local 180 / 12009 s after the restart
audit. First new complete checkpoint will be **local 1000 / 12050 s** and needs
both existing audits. Do not reuse the old PID/start pair in engine profiling:
the retained-handle pause/resume helper must receive the new identity above.
Do not launch another cook merely because the next snapshot is pending.

## Still open

Normal playable map, collision, captured data, installed 4950 s fields and
nonlinear-solver OFF state are unchanged. No new build, motion, visual, collision
or performance acceptance. The existing 25.003520 FPS / p95 48.329 ms remains a
failure against 30 FPS. The cap source-interpretation decision remains pending,
and South Fork remains ahead of Colorado, Pacuare and Futaleufu. Crew/all-scene
review and final release work remain in the full queue.
