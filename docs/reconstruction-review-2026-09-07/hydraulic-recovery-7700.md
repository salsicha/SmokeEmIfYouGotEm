# Exact hydraulic recovery after host restart

2026-09-18 UTC. The preceding commit-only turn confirmed a clean tree but made
no goal progress. This turn restores the interrupted hydraulic evolution; it
does not deliver a visible scene change or complete the physical water model.

## Stopped run and retained checkpoint

An elevated process inventory finds no `raftsim_cartesian_cook.exe` before
recovery. The old PID28776 and unified session93831 are absent. The host reports
last boot at 2026-09-17 23:24:23 America/Los_Angeles. The old run's final progress
record is local10850/time7742.5000000194013, but its last complete snapshot is
local10000/time7700.0000000192467. No exit code or successful completion is
claimed. The reboot is consistent with interruption; the process observation,
not an unchanged progress file or an observation timeout, establishes stopping.

The restart uses ONLY that complete7700 snapshot, already verified by both
state and artificial-bank audits. The partial7742.5 progress record is not a
restart state. All old inputs, reports and snapshots are retained.

## Verified native continuation

Input: `tmp/control-ablation-7700to9000s-input-v1-20260918/manifest.json`.
SHA256 `91eeedea64e150782d2cb60bb19a03a310e76dfd5dea609c7f569765c248998e`.
Output: `tmp/control-ablation-7700to9000s-workers8-v1-20260918`.
The unchanged executable is
`tmp/solver-worker-limit-v1-20260917/raftsim_cartesian_cook.exe`, SHA256
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
It runs26000 unchanged0.05-second steps to9000 seconds, with snapshots every1000
steps and eight worker lanes. No new context, cells, water or altered boundary
forcing are introduced. Measured surface geometry and inferred submerged bed
retain their original provenance; this continuation does not recalibrate either.

The independent native restart audit passes all5,382,400 cells: h/u/v and the
checkpoint clock are bit-exact. All retained physical settings, bed, grid,
roughness, boundary definitions, features and probes match. The independent
volume summation error is1.862645149230957e-9m3, below the unchanged1e-6m3 gate;
no volume correction is applied. Report:
`tmp/control-ablation-7700s-strict-restart-v1-20260918.json`, SHA256
`4dfdef4badb0ccdf09b6fa9199144ebd27214e7419599257ea3c7a81b556d488`.

All34 restart retention/metadata controls pass in2.20s. The initial sandboxed
test invocation could not access the existing pytest installation; the elevated
rerun passed using those same local dependencies. Report:
`tmp/restart-7700-controls-v1-20260918.xml`, SHA256
`1857d3b3793aea19c5a20a4c6b4bc77a50887d77353dbe1005c65a6be089fbf2`.

An independent comparison of11 progress records (local0..100, every10 steps)
against old local10000..10100 finds EXACT equality in time, total volume,
maximum depth, maximum speed and all four exterior fluxes. Wall-clock timing
and restart-relative cumulative bookkeeping are intentionally not compared.
These aggregate repeatability checks supplement, not replace, the full-array
native reload audit. They do not prove full-array equality at subsequent times.

## Live identity and next acceptance work

At this review the new process is LIVE: PID8900, exact direct process startUTC
`2026-09-18T06:34:59.2598919Z`, unified session68256. It was observed advancing
through local140/time7707.0000000192722. Revalidate this exact identity before
any process control; this written record is not proof of future liveness.
The old PID28776 must no longer be used by profiling or follow-up checks.

Next7750 is now LOCAL1000, not the interrupted run's local11000. Require its
completion marker and BOTH state and artificial-bank audits. Installed4950
water remains unchanged:7700 outflow102.74726920680162m3/s exceeds
inflow45.30695454719997m3/s, so settling is NOT accepted.

The nonlinear runtime stays OFF. Actual-profile conservative mass/momentum,
joint interface and wetting/topology evolution, visible terrain/crest/froth/
contact quality and the30FPS/p95<=33.333333ms gate remain unfinished. The latest
ordinary p9541.7264ms still fails. South Fork precedes Colorado, Pacuare and
Futaleufu; Chilko/Zambezi reviews, crew, normalization,13 retained physical
regressions and release checks remain in the full goal. Troublemaker remains a
rapid inside South Fork, never a separate menu scenario.
