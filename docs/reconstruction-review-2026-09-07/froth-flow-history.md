# Actual time-dependent froth departure audit

2026-09-18 UTC. Diagnostic evidence, not a visual, physical, performance or
release pass. Recorder and tests are committed in `c14bc1ecb`; no material,
foam source, geometry, contact, simulation frequency or ordinary-play setting
changes. Troublemaker remains a rapid within South Fork.

## What was recorded

Non-shipping `-RaftSimFrothHistoryAudit` requires an explicit
`-RaftSimDetailSnapshot=PREFIX`. After each successful native detail advance,
the recorder retains the exact flow input, start/end simulation clocks, source
sample time and lattice registration. Identical consecutive inputs coalesce;
window moves retain each original registration, while explicit teleports reset
history. Complete intervals crossing the 1.25-second retention boundary remain.
Normal play does not copy or export these arrays. Existing output is never
overwritten; the complete history index is written after its payloads.

The normal South Fork FullReach scenario at review station 8330 produced three
paired snapshots, at simulation times 9.933333851, 14.950000780 and 19.933334373 s.
Each has ten original input intervals. The analyzer integrates backward in
reverse chronological order, splitting exactly at input changes. It does not
interpolate across time discontinuities, invent missing older history or use
later input outside its interval. Final flow and registration must match the
paired completed snapshot. Original inputs are hashed and rechecked.

Reference trajectories use RK4 with maximum steps 1/128 and 1/256 second.
Every 0.25/0.5/0.75-second comparison passes the unchanged 0.1 mm maximum
convergence gate with identical reference support. Across all nine comparisons,
the largest convergence difference is 0.0499572 mm. Unsupported rows are kept
as nulls, and both individual and common cohorts are reported.

## Measured result and decision

At 0.75 seconds, for the identical supported foamy cohort (resolved coverage
above 0.1), RMS departure errors against the historical reference are:

| Snapshot | Common foamy cells | Straight latest (m) | Frozen midpoint-8 (m) | Frozen RK4 (m) | Historical midpoint (m) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00 | 1890 | 0.210201 | 0.00173615 | 0.000164164 | 0.000148391 |
| 01 | 2455 | 0.187387 | 0.00163348 | 0.000430145 | 0.000143555 |
| 02 | 2378 | 0.182281 | 0.00171036 | 0.000384701 | 0.000154874 |

The all-common wet-interior cohorts contain 6697/7403/6871 cells out of
7390/7560/7002 selected cells. Frozen-RK4 RMS errors there are
0.000705803/0.000381634/0.000308065 m; maxima are
0.0387639/0.00901423/0.00720776 m. Small RMS is not a uniform error bound.
Historical midpoint uses maximum step 1/32 second; it is not the reference.

For these captured windows, temporal changes are much smaller than the error
from straight local-velocity tracing. This does not establish that flow history
is negligible everywhere, or measure actual bubble motion. The earlier curved
frozen-current material already failed its playable appearance review.
Consequently, do not add a GPU history material on the assumption that it will
fix the broad blurred patches. No such rendering change is promoted here.

The existing baseline recording's unmodified decoded 6-second frame was
inspected again: broad soft surface patches and smooth wave faces persist.
This is the September 17 recording, not a new motion capture. Prior irregular
coverage, micro-normal and particle-only trials remain rejected. Physical
breaking/surface shape and convincing foam breakup still require implementation
and actual engine/reference review; these numerical results cannot replace it.

## Reproduction and retained evidence

Run `physics/scripts/audit_froth_flow_history.py PREFIX --report NEW_REPORT`.
Captured prefixes are `tmp/froth-flow-history-v1-20260918_{00,01,02}`.
Reports retain every selected cell, supported/null trajectories and source
hashes: `tmp/froth-history-analysis-{00,01,02}-v1-20260918.json`.
Their SHA256 values, in order, are:

- `8ce38b5676be85615450a399c2b12a84feb2907d37612be51ec024e629540157`
- `11f1024b5d9ba8d75ad50492af535f61fabb87af0ca52a45e04dbb45ede3e861`
- `759317a465e57a6a40550df39bdc07ad1289dff19f25ce0421e0b2df0615c36f`

Editor build succeeded in 83.87 s; the existing C4701 source-footprint-test
warning remains. Native `RaftSim.Water.FrothFlowHistory`: one clean pass,
zero failures/not-run. Focused Python history/characteristic suite: 34 pass;
independent rerun before the commit: 34 pass in 2.45 s. Analytic controls include
changing uniform current, noncommuting shears, remapping, missing/dry support,
invalid chronology and mismatched original metadata/input rejection.

Native report `tmp/froth-history-native-v1-20260918/index.json` SHA256:
`827cd207eca401b38a6043528a34515d4bdba35dc68c635bd5b6fb1b5c472a08`.
Initial Python XML `tmp/froth-history-tests-v1-20260918.xml` SHA256:
`3c9e21c491dd278e476e086352077f6988b8717b5c20939e5f2a1eab27eb3816`.

Gameplay label `south-fork-froth-flow-history-v1-20260918` exited zero without
timeout, saved all three snapshots and logged no history-capture rejection.
Its 900-row CSV is diagnostic only: native NullRHI testing briefly overlapped
startup, capture performs I/O, and cook CPU increased 0.125 s across the
suspension boundary. Suspend/resume both returned zero. No FPS comparison is
claimed. The last ordinary profile remains 34.854890 FPS / p95 38.0726 ms,
FAIL30. No packaged or full-traversal qualification was performed.

The 6200/6250-second hydraulic checkpoints pass both state and exact dry-bank
audits, but are not settled or installed; see the hydraulic continuation record.
Source terrain and inferred bed/flank provenance remain unchanged. South Fork,
then Colorado, Pacuare, Futaleufu, the Chilko/Zambezi water reviews, crew,
normalization, physical regressions and release queue all remain open.
