# Post-handoff accuracy and bounded batching — September 13, 2026

This follows the [consistent hydrostatic polynomial correction](normal-river-hydrostatic-polynomials.md).
The first-handoff comparison remains a pass. Longer post-handoff accuracy and
sustained owner throughput do not pass. No diagnostic result promotes the new
solver into normal display/contact water.

## Longer eight-slot comparison: local accuracy still fails

Independent CPU job79125 exits0 with a valid failure report:
`tmp/south-fork-compensated-two-moves-comparison-v1-20260913.json`.
Its live input `tmp/south-fork-compensated-two-moves-owner-v1-20260913.json`
has SHA256 `d783ecd5d8cb48972ad3262c61a17dcdef9868fd766cb7dbf89e96bf17dcc0bf`.
At6.3333336636424065s, after the first move at3.9333335384726524s:

- Maximum state error0.002101234931135565 fails the unchanged1e-4 local gate;
  94 cells exceed the gate.
- Worst y58/x32/hu: GPU-5.749593734741211, CPU-5.7516949696723465.
- Component-relative errors8.561089050306862e-6,1.0098221840821816e-5,
  1.880806069613397e-5 individually pass2e-5, but do not override the local failure.
- Window inventory maximum error5.287853530155928e-6 and GPU float water-balance
  residual0.0002489304477819587m3.

The independent CPU implementation is unchanged. The live owner also failed
its16-observation capacity before the requested second move. These are separate
accuracy and throughput failures; neither is hidden by the passing first move.

## Sixteen-slot scheduling experiment

The observed native source intervals frequently span16 unchanged1/120s GPU
steps. The previous eight-slot graph cap needs at least two graphs for those
intervals, plus asynchronous completion handling. A shared host cap now permits
1..16 slots in the advance API, owner and explicit diagnostic arguments. The
default diagnostic remains4; no normal gameplay opt-in was added. Total4096
trials per interval, timestep/CFL policy, acceptance tolerances, queue16 and
maximum two run-ahead graphs are unchanged. This is scheduling, not a larger dt.

Tests retain all original controls and add16-slot graph partition comparisons
for successful, rejected, fatal, exhausted and inactive transactions. They require
bit-exact state, clock, counters and diagnostics. Owner tests now cover
three clock/interval configurations, four slot counts1/4/8/16, and both0/2
run-ahead settings. Invalid0/17 budgets must fail before dispatch. For the
longer clock case,16slots/run-ahead0 completes32 accepted steps in two graphs
versus four graphs for8slots; both retain the intended initial interior exactly.

Initial native7348 exits0 with113 clean tests plus one descriptor-cache warning
in the enlarged advance stress test. All numerical assertions pass, but this
is not reported as clean. The eight independent advance cases and descriptor
checks were separated into automation frames so transient GPU descriptors
recycle, preserving every assertion/direct control. Native95009 then exits0:
122 clean tests, zero warnings/failures,30.197794s.

Build37979 succeeds42.27s;63916 succeeds15.75s; final56991 succeeds15.73s.
Final WaterDetail DLL SHA256:
`6e9fefd4b2f349fb2fff65a89e1c107ce01b2b63607a3c4a50b47c255a2befd2`.
Raft DLL: `5c65139d2f537dda134836b73b961d347155e3be8377704ee69eb8c25556cb0d`.
The transport shader/independent CPU equations did not change this turn.

## Actual sixteen-slot result: still fails capacity

Capture21693 exits0, cook suspension/resume both0, but its actual owner report
`tmp/south-fork-sixteen-slot-owner-v1-20260913.json` fails with the same full
queue/no-time-discard message. It completes58 intervals and one move, not the
requested two. Published completed time7.466667056083679s, retained state
7.581101276484915s, remaining0.018899118527770042s, next proposed
dt0.004166666883975267s. Latest retained source9.266667149960995s.
There are16 retained observations,888 accepted steps in completed intervals,
139 graphs and68 run-ahead graphs. The longer stopping time is not a sustained
capacity pass or an isolated speedup proof; the live source trajectories differ.

Diagnostic frame audit `tmp/south-fork-sixteen-slot-frame-v1-20260913.json`:
10.130425FPS,p9581.5572ms,maximum6062.7637ms, CSV rows60–240. It includes
diagnostic capture/serialization and must not replace the latest ordinary
gameplay performance measurement. It fails30FPS and is not release acceptance.

## Next isolation

The recorded-stage diagnostic now admits bounded observed moving-window streams,
validates exact same-time/integer retained overlap of state, bed and reference,
and uses the real GPU conservative transfer before subsequent stage evolution.
It still requires exact final clock, move count and bit-exact live final state.
The source array limit matches the bounded owner capture256; stage byte budgets
remain128 v1 or64 polynomial v2 records. No source endpoint is resampled and no
interior is reset. A fresh replay of the failing eight-slot input is capturing
6.0–6.34s stages while evolving from its original first observation.

That replay66474 now exits0:752 evolution trials, one actual move,40 captured
trials/80 stages, exact final6.3333336636424065s clock and bit-exact failing live
state. Trace `tmp/south-fork-postmove-stages-v1-20260913.json` SHA256
`fbb061508782eb2c5fe727d4b6b5c46bfbc7721e28e85b0b853e3bd579e54a76`;
binary SHA256 `1dfc4afbd4e9034f4acbe4a987108b8457a18862a047beaa170c139208947312`.
Independent operator comparison15085 exits0:
`tmp/south-fork-postmove-operators-v1-20260913.json` has maximum transport
error0.00015720816958642025 and pressure-force error2.894001594277995e-5.
These are much smaller than the earlier bank-polynomial defect; the accumulated
post-move error is not yet explained. A fresh capture of3.9–4.9s covers the
handoff and its first second, without changing the evolved source or solver.

Handoff replay87958 exits0 with120 captured trials/240 stages over3.9–4.9s;
middle replay12603 exits0 with120 trials/240 stages over4.9–5.9s. Both replay
all752 steps and the actual move, with bit-exact final failing live state.
Independent comparisons86518 and65068 exit0. Maximum transport/pressure-force
errors are0.000111956680/1.983706504e-5 for the handoff and
0.000116997954/2.715520439e-5 for the middle interval. Reports:
`tmp/south-fork-handoff-operators-v1-20260913.json` and
`tmp/south-fork-middle-postmove-operators-v1-20260913.json`.
These do not identify a large same-input operator defect. The5.9–6.0s gap and
pre3.9s history are not covered by these captures.

Important: the passing first-handoff live run has DIFFERENT source observation
times from this failing longer run, beginning at observation3. Its passing
CPU checkpoint must not be reused as this run's initial condition, and does not
prove this run was accurate before the handoff. Error onset remains unknown.

Added an optional read-only endpoint observer to the independent moving replay;
its equations, timesteps and acceptance gates are unchanged. The new
`physics/scripts/audit_recorded_state_history.py` matches exact captured stage0
endpoints only after requiring identical live-source bytes, exact origin/time,
qualified final replay and consistent duplicate states. Invalid indices and
unvisited endpoints fail explicitly. All42 focused Python tests pass, including
observer numerical identity, malformed endpoint rejection and30FPS budgets.
CPU history job97458 is running from the original first observation, with report
`tmp/south-fork-recorded-state-history-v1-20260913.json`; no state reset.

Next inspect that independent state history, then address the actual error and
bounded owner service cost. Preparation/finalization of inactive graph slots
still executes even when pressure recurrences are culled; potential savings
must preserve initialization, rejection, clock and inventory semantics.
Normal shared render/contact integration, outer-domain departed wave/foam
persistence,30FPS, terrain/rapid/crew quality, later rivers and release/final
commit requirements all remain open. The long cook is unchanged;5600s passes
both state/artificial-bank checks but remains settling;5700/local34000 is next.
