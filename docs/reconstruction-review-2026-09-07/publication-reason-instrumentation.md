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

## Exactly one follow-through owner

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
