# Qualified offline workers and exact South Fork continuation

2026-09-17. This accelerates the active reconstruction dependency. It does not
change the playable scene, solver equations, geometry, or acceptance thresholds.
Source implementation is committed in `6dc257ebc`.

## Execution-only change

The standalone Cartesian cook accepts an optional fifth argument: maximum total
execution lanes, including the caller. Valid values are 1..64, bounded by host
hardware concurrency. The default remains four, including in gameplay. The
one-shot configuration must precede pool initialization; repeated or late
configuration is rejected. No live pool is resized. Rounding-mode propagation,
work partitions, serial reductions, timestep and all state gates are unchanged.

Example syntax (always use a fresh output directory):

```text
raftsim_cartesian_cook.exe manifest.json fresh-output-directory steps frame-interval 8
```

Six native CTest cases pass, including the complete Cartesian domain suite at
default, one and eight lanes. Fourteen comparison CLI/record tests pass; the
combined comparison and restart-metadata suite passes 20 tests. Invalid lane
requests are rejected before nonexistent inputs are accessed or outputs made.
No physical failures from other suites are waived by these results.

## Full-river qualification

Four fixed alternating-order pairs evolve the same 841-tile, 5,382,400-cell
3600 s checkpoint for 20 steps at the unchanged 0.05 s timestep. Every physical
progress record and all saved h/u/v arrays match exactly in every pair. All
4,206 original input files are verified unchanged. There are 24 paired array
comparisons, not 24 distinct evolved times. The original cook was suspended by
its verified retained process handle during these pairs and resumed afterward.

| Pair | Order | Default four lanes, seconds | Eight lanes, seconds |
| --- | --- | ---: | ---: |
| 0 | Default first | 16.1506153 | 12.2028534 |
| 1 | Eight first | 17.1324313 | 11.7803657 |
| 2 | Default first | 17.2298864 | 11.9079729 |
| 3 | Eight first | 17.0233192 | 12.0056632 |

Median solve/capture time falls 17.07787525 -> 11.95681805 s, approximately 30%.
These include initial snapshot writes and inspections, exclude startup before
the initial progress record, and are NOT game-frame timings or settling proof.
Both orders and every pair improve; no failed or slower pair was discarded.

Comparison: `tmp/solver-worker-eight-pairs-v1-20260917/report.json`, SHA256
`b335342a76dff5090ba39dbc5e3e93efef59489c083576c5cae1eddcfcabf58c`.
Qualified executable: `tmp/solver-worker-limit-v1-20260917/raftsim_cartesian_cook.exe`,
SHA256 `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.

## Actual handoff, not an observation-timeout restart

Both 4850/local25000 and 4900/local26000 snapshots of the original cook pass
independent state and artificial-bank audits. All 86,720 artificial bank cells
remain exactly dry. At 4900 s, maximum depth is 3.750272005 m, speed 6.236676347
m/s and volume 2,843,376.488222 m3. Maximum step conservation residual is
1.521822357e-8 m3. Outflow 114.200305260 versus inflow 45.306954547 m3/s is
still far from balance: NOT settled, NOT promoted.

A fresh immutable restart was prepared from the completed 4900 s checkpoint;
no source terrain, boundary, roughness, initial water or context was added or
retuned. The still-live original PID17516 was paused only after its exact
executable and start identity were verified. Replacement PID6968 started at
`2026-09-17T19:38:25.9811777Z` with eight lanes, 10,000 steps and snapshots every
1,000 steps, continuing the same clock to approximately 5400 s.

Independent native restart auditing verifies all 5,382,400 original cells
bit-exact, unchanged grid/bed/roughness/boundaries, zero added water, and the
identical time. Initial h/u/v file hashes also match the original checkpoint.
Initial state and bank audits pass. Only after those checks and 20 successful
new steps was the original retained process terminated. All old files remain.
Its last progress was 4928 s; that post-checkpoint 28 s interval is recomputed,
not skipped. Conservation ledgers restart per segment; retain both histories.
This is an intentional qualified execution upgrade, not a timeout recovery.

The first 40 overlapping progress records, through 4919.5 s, also reproduce the
original clock, volume, maximum depth/speed and all four boundary fluxes exactly.
Report: `tmp/control-ablation-workers8-overlap-progress-v1-20260917.json`.
These are aggregate diagnostics, not a new full spatial-state comparison; the
bit-exact spatial checks are the native initial-state audit and paired runs above.

- New input: `tmp/control-ablation-4900to5400s-input-v1-20260917/manifest.json`,
  SHA256 `bff79d8af697e8948051345c75d1cf309d0bfb3d3ea6f89f1f3eb8252f0ee764`.
- New output: `tmp/control-ablation-4900to5400s-workers8-v1-20260917/`.
- Handoff: `tmp/control-ablation-workers8-handoff-v1-20260917.json`, SHA256
  `2a2dd7265d14c6caa9645913e07e6dea943e11484426d54a2de861561f077061`.
- Native restart audit: `tmp/control-ablation-4900s-workers8-restart-v1-20260917.json`,
  SHA256 `58458e67d8309f846c5ff4a7452a977576b90a1c65349025fa8e4171e39925d7`.

The installed gameplay DLL remains byte-identical at SHA256
`09a1dc5804bdd57a119d8f074af0191282c77f162ddcaecd37ffc6d7110285ef`.
No new visual, reference-motion, settled-flow or 30 FPS acceptance is claimed.
Captured terrain and inferred submerged-bed provenance remain distinct.

Next completed 4950 s / local1000 in the NEW output requires both state and
dry-bank audits. Revalidate PID6968's exact start/executable for profiling;
PID17516 is terminal and must not be reused. Continue source-consistent terrain,
rapid shape, physical breaking/froth and normal-play performance, then Colorado,
Pacuare, Futaleufu, Chilko/Zambezi, crew, normalization, regressions and release.
Troublemaker remains a rapid inside South Fork, not a scenario/menu entry.
