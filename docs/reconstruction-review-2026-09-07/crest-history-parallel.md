# Parallel mapped crest history in normal play

September 19, 2026 UTC. CPU scheduling improvement; not geographic, breaking-wave,
30 FPS, collision/traversal or release acceptance. South Fork remains unfinished.

## What changes

Changing-coordinate crest histories now read the original coordinate map and
update independent vertices in joined 256-vertex batches. Rebuilding that map
still uses the original serial insertion order and duplicate-coordinate
last-writer ownership. Owner lookups join before swapping history buffers.
Unchanged-coordinate (dense) and empty histories remain serial. No geometry,
blend expression, temporal cadence, threshold, normal, foam, support, collision,
solver or water-field content is changed or omitted. Ordinary play needs no
enable flag; `-RaftSimSerialCrestHistory` retains the same-binary control.

The detailed baseline identified 2.014033 ms mapped versus 0.371560 ms dense
history work. It also found genuine profile changes on every rebuilding frame;
there is no evidence supporting bypassing those geometry changes. The baseline
is instrumented and is not the ordinary performance qualification.

## Evidence and rejected variant

The first all-history parallel variant is REJECTED: although mapped history
improved, one dense/order group regressed from 0.338700 to 0.350499 ms. Its
[complete pair receipt](crest-history-parallel/rejected-all-history-a.json)
is retained, not folded into a successful average.

The revised mapped-only candidate passes two actual FullReach game comparisons:
64 consecutive frame pairs per run, every vertex attribute and correction
checked. Order alternates every TWO frames, so the commonly alternating dense
and mapped states each exercise both execution orders. Copies/comparison are
outside measured history work; scheduling and joins are inside it. Each history
maintains its own evolving state from the beginning of the run.

| Run / state / first path | Pairs | Serial mean ms | Candidate mean ms |
| --- | ---: | ---: | ---: |
| B / mapped / serial | 18 | 2.165239 | 0.993861 |
| B / mapped / candidate | 17 | 2.143535 | 0.987936 |
| B / dense / serial | 14 | 0.418721 | 0.431543 |
| B / dense / candidate | 15 | 0.409040 | 0.457280 |
| C / mapped / serial | 16 | 2.047818 | 0.984862 |
| C / mapped / candidate | 16 | 2.040080 | 0.968444 |
| C / dense / serial | 16 | 0.375963 | 0.471513 |
| C / dense / candidate | 16 | 0.329469 | 0.415856 |

All 67 mapped pairs improve. All 128 pairs match, and runtime dispatch confirms
dense histories execute serially. Dense timings nevertheless favor the original
history instance; these are separate buffers in a dual-history audit, not a
dense-path speedup. Do not hide that result or claim every frame gets faster.
Run B publishes original history; C publishes the then-opt-in candidate.
[B receipt](crest-history-parallel/mapped-only-b.json) and
[C receipt](crest-history-parallel/mapped-only-c.json) retain every pair and hashes.

Four native regressions pass with zero warnings/failures/skips/in-progress tests
in both revised-candidate v2 and default-enabled v3 reports. The independent
36-frame history oracle covers duplicates with different targets/boundaries,
sparse moves, reordering, translation, shrink/growth, changed source prefixes,
empty/reset and zero/unit/intermediate blending. The mapped-only scheduling
assertion is also tested. Seventeen Python audit/stage tests pass. The auditor
rejects missing/duplicate/reordered/nonexact rows, wrong order, malformed or
invalid timings, incomplete state/order groups and incorrect mapped-only dispatch.

Raw evidence uses labels `south-fork-parallel-history-pair-{b,c}-v2-20260919`
under `unreal/Saved/Logs`, `Profiling/CSV` and `RaftSimValidation`.
Owned cook 12672 and exact source replay 14076 were safely suspended/resumed
through retained, start-time-validated handles for each actual-game comparison.
B cook's suspension CPU bracket is 0.125 s, C's is zero; B replay's is zero,
C's is 0.015625 s. All suspend/resume statuses and game exits are zero.
These brackets are recorded, not claimed as zero-load guarantees.

## Hydraulic continuation, not playable promotion

Both native-state and exterior-bank audits pass at 12,250/local5,000 and
12,300/local6,000. All 5,382,400 cells are checked; all 86,720 artificial-bank
face cells remain exactly dry. At 12,300 s maximum depth is 3.992421 m,
speed 5.380165 m/s, and maximum step conservation residual 1.262257e-8 m3.
Combined outflow is 107.132216 m3/s versus 45.306955 inflow: NOT settled.
The [four audit receipts](crest-history-parallel/) retain native field hashes.
Do not replace installed 4,950 s fields with these transient checkpoints.

No map, terrain, collision or captured source is changed. Nonlinear runtime
remains OFF. The cap source-fidelity decision is still pending; no assumed
permission or source-exact claim. Colorado, Pacuare and Futaleufu remain queued
behind South Fork. These paired diagnostics alone are not scene acceptance.

## Rebuilt default and normal starting point

Final editor and standalone Development builds succeed (22.41 and 194.85 s).
The game build retains the preexisting potentially-uninitialized `Current`
warning in `RaftSimDetailSourceFootprintTest.cpp:105`; no new compile error.
Build/test logs and binary hashes are retained in the delivery receipt.
This is not a newly packaged-content release or a standalone-executable launch.
The actual captures use the rebuilt editor's `-game` normal scenario path.

The final normal-start capture has no crest-history enable flag or rapid-review
station. It loads South Fork Full Guided Descent near station 120 m, progressing
from 120.193 to 135.367 m across 24 player-view images. The 15.604 s movie fully
decodes to 468 frames from 232 engine source frames; 36 decoded consecutive pairs
after the first second are identical. Encoder 30 Hz is NOT game FPS. Three source
screenshots 000/012/023 and unmodified decoded 3/13 s frames were inspected: raft,
camera and water progress; no obvious new split surface in these views. Soft
water, coarse/repeated canopy, crew overlap/fit and lighting/temporal artifacts
remain. This calm starting section does not validate Troublemaker's breaking
waves, shoreline stability throughout the river or photographic realism.
The menu was not clicked; the normal scenario/map is launched directly.

At 10.021497 s, 2,033 independent barycentric presented-water/support probes have
zero dry, unavailable or ground-occluded points. Maximum support/carrier error
is 0.000190415 cm, RMS 0.000109171 cm, including paired resolved detail. This is
not full-hull collision, traversal, GPU upload/latency or physical-water accuracy.
Raw contact evidence is `tmp/parallel-history-startup-contact-v3-20260919.json`.
The [startup process receipt](crest-history-parallel/startup-process.json)
retains all image/movie hashes and flags; the [decoder result](crest-history-parallel/startup-motion.json)
supersedes its initial `fully_decoded:false` without changing acceptance flags.

## Ordinary frame cost: mixed, still fails 30 FPS

Four uninterrupted runs use the same final binary in serial/default/default/serial
order, 900 frames each, all rows 60–840, D3D12 1280x720, four solver lanes,
the normal FullReach scenario at review station 8,330, and no pair audit,
screenshots or motion recording. Runtime logs confirm default UE frame-time mode;
workload association uses its one-row offset. Physics and quality are unchanged.

| Run | FPS | Mean frame ms | p95 ms |
| --- | ---: | ---: | ---: |
| Serial A | 26.181311 | 38.195185 | 45.9455 |
| Default B | 24.953169 | 40.075070 | 48.0971 |
| Default C | 25.497627 | 39.219336 | 47.2092 |
| Serial D | 24.648864 | 40.569821 | 48.6359 |

Every run fails the unchanged p95 <=33.333333 ms budget. Forward comparison
regresses; reverse improves. These variable trajectories/shared-host timings
do not demonstrate a reliable whole-frame gain. The retained default is supported
by the repeatable, exact same-input mapped-history saving, not an FPS pass.
The [complete metrics and process receipts](crest-history-parallel/ordinary-frame-cost.json)
retain all four outcomes, CPU/thread/GPU and nested water metrics, raw CSV/log
hashes, exact arguments and both workload suspension/resume records. All games
exit zero without timeout; all suspension/resume statuses are zero. Cook CPU
brackets are zero in all four; replay C has 0.015625 s, others zero.
No build, native test or scientific audit ran during these four captures.

Next work remains actual water/rapid realism, frame cost and exact hydraulic
coupling, not a later-river promotion. Cook 12672 and source replay 14076 are
resumed; preserve their identities and protected source files. Next complete
hydraulic checkpoint after local6,000 needs BOTH audits. Source case1 has not
yet produced a completed report. No repeat source solve or duplicate cook.
