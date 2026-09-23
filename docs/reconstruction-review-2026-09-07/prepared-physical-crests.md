# Prepared physical crest constants

September23,2026 UTC. New performance trial, not a new physical wave model or
river acceptance. The previous goal turn delivered referenced crest storage
in normal South Fork play; this investigation targets remaining profile cost.

## Candidate distinction and invariant

`RaftSimPreparedPhysicalBreakingSample` computes site-constant clamps, support
limits and lobe widths/centres once for an immutable physical profile. The
original8m spatial index, ordered site subsets, owner cap, coordinate transforms,
float operations, divisions and five exponential evaluations remain. No reciprocal
substitution, reduced tolerance, coarser grid, skipped lobe, altered height,
foam source, or stale profile is introduced. Unsupported/legacy inputs use the
original evaluator. Prepared tables own their data and copies remain independent.

This differs from the previously rejected inline-only evaluator: it moves
constant arithmetic out of the repeated query, rather than only specializing
the call. Preparation and extra tables still have costs and must be included
in ordinary frame measurements. The candidate is currently explicit non-shipping
`-RaftSimPreparedPhysicalCrests`; its query comparison uses
`-RaftSimPreparedPhysicalCrestAudit`. Neither is a normal-play default. Competing
full-scan/fine-index/inline switches prevent this path from activating. Other
scenarios are excluded. The existing compact crest-storage default is retained.

## Native and report validation

Editor v1/v2 builds pass57.83/41.12s. Existing C4701 footprint and C4305 D6
warnings remain; this is not a warning-free build. Native v1 passes three tests,
including166,388 indexed/full/prepared query comparisons. V2 adds mixed/all-zero
height emitters, whose height-only path can be zero while foam remains active:
199,806 exact height/foam comparisons pass, along with ReferencedWaterVertices
and ShorelineFineCrest. Controls include mixed global/local caps, both site
orders, non-unit directions, tile/support boundaries, empty and sparse indexes,
copied prepared storage, legacy and invalid-index fallback. These are synthetic
numerical comparisons, not measured river geometry or convincing motion.

The first actual-game audit exits0 and logs zero numerical mismatches, but the
original report validator FAILS because startup legitimately creates two profile
epochs in frame1. That rejected log is preserved; it is not edited into a pass.
V2 gives each native epoch a unique consecutive ID, separately recording its
frame. The validator still rejects duplicate/missing/out-of-order epochs, regressed
frames, any mismatch, malformed rows and fewer than64 nonempty epochs. Distinct
same-frame epochs are accepted only with their own IDs. All25 focused report
tests pass, including both this distinction and missing-middle-epoch rejection.

## Actual query qualification and rejected default promotion

The corrected300-frame actual-game audit checks148 nonempty profile epochs and
23,098,795 queries with zero mismatches. The final zero-query epoch is retained.
[Query qualification](prepared-physical-crests/query-qualification.json) binds
the native output, tests, initial failed parser log and v2 binaries. This proves
numerical query equivalence for the exercised inputs, not scene acceptance.

Four recording-free900-frame runs use the same v2 editor binary and the fixed
60..840 interval; native timing mode is confirmed with scope offset1. No query
audit overhead is included. [Cost receipts](prepared-physical-crests/ordinary-cost.json)
retain CSV hashes, selected complete metrics, full report hash and per-run
source suspension/resumption receipts.

| Run | Path | FPS | Mean frame ms | p95 frame ms | Mean crest update ms |
| --- | --- | ---: | ---: | ---: | ---: |
| A | Reference | 26.777125 | 37.345309 | 45.4307 | 4.813441 |
| B | Prepared | 27.038815 | 36.983869 | 45.8275 | 4.693580 |
| C | Prepared | 32.231831 | 31.025231 | 42.0052 | 3.715676 |
| D | Reference | 32.269931 | 30.988601 | 41.7805 | 3.783524 |

Default promotion is REJECTED: B improves mean over A, but C is slightly slower
than D; both candidate p95 values are worse than their neighboring controls.
The large improvement between the first and second pairs also affects the
reference, so it cannot be attributed to preparation. All four fail the30FPS
p95 budget of33.333333ms, including the two with mean FPS above30. The candidate
remains explicit opt-in only; do not repeat this unchanged trial seeking a pass.
This is supporting qualification and a rejected performance hypothesis, NOT a
new visible delivery or a normal-play FPS improvement.

## Final normal-path check and limits

The standalone Development game rebuild passes in74.34s; the existing C4701
warning remains. Final12 parser tests pass, in addition to the earlier25 focused
and three native tests. No C++ changes followed the v2 native qualification.
[Reference validation](prepared-physical-crests/reference-validation.json) binds
the rebuilt executable, editor DLL and final checks. The actual launch uses
editor-hosted D3D12 `-game`, normal South Fork scenario start, no review station
and no prepared override. It confirms compact storage ON and no prepared-path
activation. This does not claim a packaged executable traversal.

The launch exits0 after24 captured views and15.564s recorded motion; all467
encoded frames decode, including39 exact adjacent repeats. Recording rate is
not game FPS. Inspected decoded1/6/11s views show the briefing fitting/fading and
no new bank/water gap in those views. Broad smooth foam, coarse canopy and early
crew shading remain; this is not convincing-water or full shoreline acceptance.
All2,034 sampled wet support points agree with submitted triangles within
0.000191cm;8,645 retained source anchors have zero foam/bulk channel error.
These limited probes do not establish full-river collision or GPU upload parity.

Captured geometry/collision/installed4950 fields
and the known-unqualified nonlinear path remain unchanged. Source qualification
PID6480/start2026-09-23T15:18:43.5347928Z is still the sole live scientific job;
no cook/source replay is duplicated and no protected source implementation changed.
The complete South Fork reconstruction, ordered Colorado/Pacuare/Futaleufu,
all-scene water, crew, normalization and release requirements remain open.
