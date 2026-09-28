# Counted water publication reasons and recenter timings

September28 UTC. Instrumentation built; actual-game attribution is PENDING.
This follows [the retained v15r2 event evidence](v15r2-publication-events.md),
not a new water appearance, physics, performance or reconstruction delivery.

## Runtime scope

The normal water actor now records the four actual caller reasons for
PublishLiveVolumeCore: interpolation, carried recentre, missing-section
creation and hard swap. Each caller increments its reason once, and the
callee independently counts all attempts, including rejected inputs. These
are not GPU-success counters. Tick seeds inactive count columns with
Accumulate0, without clearing initialization or other-actor work in the same
CSV frame. Zero measured time is never treated as proof of no call.

CPU scopes separate RecenterWork (after the no-work early exits), planar
coordinate/tangent mapping, recenter state-history shifting, rendered-history
carry and each reason's publication call. RecenterWork includes planar and
state-history work; reason scopes include CartesianPublish and crest work.
Do not add nested timings. RecenterWorkCalls counts entering the work path,
not proof that clamping produced a nonzero displacement.

No update was removed or reordered. The original interpolation alpha,
recentre carry, fine-crest history, sampling, geometry, material, hydraulic
settings and acceptance thresholds are unchanged. The source diff consists
of timing/count macros and their lexical scopes. Existing user edits remain.

Single-worker Editor Development build session58485 completed exit0 in
163.22s; log `tmp/publication-reasons-build-v1-20260928.log`. It ran alongside
the hydraulic solve, so its duration is not a performance comparison. No game
timing ran alongside that solve. Built source SHA256:
`3c600d57a90946468070c9874b6fdec25cf6bfe1cf91343cba69cc6d3b6a13d0`.
RaftSimRaft editor DLL SHA256:
`88b3c5f6acfba5254b5e4e793ea15e09341441ef323b0baa587fab05d92969e2`.
The existing v15r2 packaged game is unchanged.

## Strict evidence reader

`physics/scripts/audit_water_publication_csv.py` uses the existing completed
CSV validator and reads the verified final header for appended series. Within
the requested interval, every reason/count must be present, finite,
nonnegative and integral; reasons must sum to the independent callee count.
An active counted branch requires its CPU scope. Inactive missing timings
remain unavailable rather than zero. Reports retain the whole interval,
caller groups and all multi-publication/recenter event rows. They do not
associate elapsed FrameTime by correlation or claim causal speedups.

Nine new regressions cover partitions, missing/ambiguous/invalid data,
count-vs-timing distinction, intervals, completed headers and late-appended
scope availability. Together with the cadence and frame-CSV suites:36 pass.
This proves parser behavior, not actual runtime branch attribution.

## Terminal capture and recovered analysis (September28 UTC)

Session60320/wrapper4504 is terminal. Its single editor-hosted normal-config
8310 capture completed1200frames and exited0 with zero runtime errors. The
subsequent analysis failed only because the wrapper supplied the historical
`--ignore-duplicate-unmeasured-header NumInstanceTransformUpdates` option,
but that duplicate is ABSENT in this capture's completed CSV header. The
strict reader correctly rejected the stale exception. Original failure receipt
is preserved. Re-running ONLY the reader on the same saved CSV without that
option succeeded on all1140selected rows, with three target events. No parser
gate was weakened, data modified or game capture repeated.

Actual caller attribution is now available:

| CPU row | Interpolation publication (ms) | Recenter publication (ms) | Recenter work (ms) | Carry history (ms) |
| --- | ---: | ---: | ---: | ---: |
| 244 | 5.1058 | 25.8433 | 2.7819 | 1.4274 |
| 547 | 6.3387 | 31.1249 | 2.9513 | 2.4803 |
| 808 | 7.2798 | 25.2545 | 3.3998 | 1.7476 |

Each event counted exactly one interpolation publication, one recenter
publication, one recenter work, one planar geometry update and one carry-history
operation. No Create or HardSwap publication was counted in rows30..1169.
The other1137rows each counted one interpolation publication only, mean12.0342ms.
Nested scopes must NOT be added: event Refresh includes recenter/publication
work, and the crest-update scope overlaps publication work. This isolates actual
callers, not a demonstrated safe way to omit publication or a measured speedup.
Preserve current rendered/fine-crest history when designing any scheduling fix.

Actual timing remains a FAIL: mean40.2654ms, p9555.2201ms, max108.504ms,
two frames above100ms, versus20FPS/p95<=50ms/no>100ms. This is editor-hosted
diagnostic attribution, NOT new packaged acceptance or an A/B performance gain.

- CSV `unreal/Saved/Profiling/CSV/sf-publication-reasons-8310-v1-20260928.csv`,
  SHA256 `5de36712e6650bdaa9bbed08fe5159a943d1b073a4f7e3b16d76ae34f059bc50`.
- Report `tmp/sf-publication-reasons-8310-v1-20260928.json`,
  SHA256 `bd97829fb69a505cf6a699ad4f57013520d5f0c8e08e3c9d3d15bb0c3737365a`.
- Launch receipt under `unreal/Saved/RaftSimValidation/` with the same label
  and `-frame-audit.json` suffix; normal configuration/runtime health pass.

Dependent spray owner15924/session71849 stopped before building because the
prior receipt was failed. Its failure is preserved too. Recovery recipe
`tmp/follow-spray-emitter-anchor-v2-20260928.ps1` checks these exact failures,
original six source hashes, captured CSV/report identity, actual runtime health
and selected-row coverage, and all original capture inputs before building.
ONE recovery owner is live: session9712/wrapper24660, start05:30:50.8818041UTC,
phase `editor_build`; receipt `tmp/spray-emitter-anchor-follow-through-v2-20260928.json`.
It performs the same single-worker build and six native tests, without another
capture, package or acceptance claim. Frozen sources remain unchanged.

## Historical follow-through launch record

- Session60320, PowerShell wrapper4504, started04:12:36UTC.
- Recipe `tmp/follow-publication-reasons-v1-20260928.ps1`.
- Receipt `tmp/publication-reasons-follow-through-v1-20260928.json`.
- Currently waiting on the exact existing hydraulic wrapper33552, whose
  observed start time is2026-09-28T03:50:05.3825805Z. Native cook39708 continues.

This owner waits for the hydraulic wrapper to exit AND requires its successful
native completion and final audits. It never stops or restarts that process.
It then rechecks frozen instrumentation/analyzer/launcher inputs, disk space
and the existing launcher's engine/build/cook isolation guard. Exactly one
1200-frame editor-hosted normal-configuration8310 capture is queued, label
`sf-publication-reasons-8310-v1-20260928`. It then runs the new strict reader
over rows30..1169 and rejects a capture with no target events. The raw launch
receipt, CSV and publication report must be inspected before drawing any
runtime conclusions. Do not start another copy while this owner is live.

Next use measured branch costs to choose the implementation, preserving
rendered history and surface continuity. Recurring changing-profile selection
cost remains distinct from rare publication hitches. Dynamic breaking, flat
foam, hydraulic settling and all river/release acceptance remain open.
