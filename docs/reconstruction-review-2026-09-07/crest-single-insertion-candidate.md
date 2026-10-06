# Single-lookup crest insertion candidate

2026-09-24. REJECTED and removed after identical-input comparison; staged v7 unchanged.

Ordered midpoint assembly previously performed Contains then Add for each new
edge. The opt-in `RaftSimSingleLookupCrestInsertion` uses FindOrAdd with the
current point count. Existing midpoint IDs are strictly lower than that count,
so equality identifies a newly inserted edge without a second lookup. No map
reference survives allocations. Triangle ordering, current-coordinate sampling,
profile tolerance and physics are unchanged.

Editor build succeeded155.64s. Native CrestEdgeHashSelection and
WaterDetail.RefinementTopologyCache each pass independently, zero warnings or
failures. Reports: `tmp/single-lookup-crest-native-20260924/index.json` and
`tmp/single-lookup-crest-cache-native-20260924/index.json`. The first command
used an incorrect cache-suite prefix and ran only the edge test; the second
verified command supplies the separate cache result. The extended edge test
compares ordered parents, triangles, owners, expanded coordinates and build/
reuse counters across24moving-profile/crop/winding/detail/epoch states.

## First actual normal-start pair

Candidate then control, same editor binary,900frames each, normal FullReach,
1280x720D3D12offscreen, default solver lanes and unchanged quality. No live
cook/game at entry, no concurrent diagnostic during either measurement.
Both exit0 without timeout and confirm nonlegacy timing. Predeclared rows
60..840 (781samples), offset1:

| Mode | Mean frame ms | p95 ms | Active selection mean ms |
| --- | ---: | ---: | ---: |
| Candidate |36.372822|44.9857|2.897084|
| Control |31.095175|41.0350|2.674532|

Report with hashes: `tmp/single-insert-first-pair-20260924.json`.
This pair does NOT demonstrate a benefit. Both fail33.333333ms. Execution-order
and trajectory effects prevent assigning the whole difference to edge insertion.
Do not promote or rebuild/package the candidate based on source simplicity or
native equality. Before further whole-frame runs, use paired identical actual
inputs to determine whether changed-mask assembly itself improves; if it does
not, remove this candidate rather than accumulate diagnostic-only alternatives.
No new visual improvement, shoreline/collision acceptance or river completion.

## Identical-input decision

Audit build passed18.05s. Actual normal-start300frame audit exited0 without
timeout, producing64pairs after2warm builds. Same current shoreline inputs,
alternating execution order, includes map construction. Every pair preserves
ordered parents, triangles, owners, expanded coordinates and production topology.

| First path | Pairs | Reference build ms | Candidate build ms | Reference assembly ms | Candidate assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reference |32|2.740241|2.770288|1.823663|1.882912|
| Candidate |32|2.772935|3.006922|1.824481|2.044253|

Report `tmp/single-insert-identical-a-20260924.json`, SHA256
`42202f893f0d57d91b5c2ed9d390f48d0cfbf8cc13ece68a12dd0f49529c1ea1`.
Both assembly and whole-build costs are worse in both orders. Candidate,
temporary audit extension and candidate-specific test additions were removed;
git confirms no remaining diff in the four affected raft files. Existing tests
and default behavior are restored. Do not repeat this unchanged experiment.
Removal editor rebuild is TERMINAL SUCCESS139.34s, log
`tmp/single-lookup-crest-removal-build-20260924.log`. Source and editor binaries
now exclude the rejected candidate and temporary audit mode.
No Game/stage rebuild is needed: the candidate was never installed there.
