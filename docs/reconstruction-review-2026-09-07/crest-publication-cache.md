# Crest ownership publication cache — not promoted

September 23, 2026 UTC. Bounded South Fork runtime investigation, not a new
visible reconstruction or a river/performance acceptance. South Fork remains
the first unfinished river; Colorado, Pacuare and Futaleufu remain queued.

## Implementation and exactness

`FRaftSimCrestPublicationCache` retains only the mapping from refined triangle
owners and original cell offsets to published cell offsets. Both complete
integer input arrays must match; no hash or assumed version substitutes for
equality. Every current triangle index is still copied on every call. No vertex,
crest, foam, normal, time history, captured geometry or hydraulic state is cached.
Changed ownership rebuilds through the existing publisher, including its
unordered-input fallback. Reset invalidates even an empty cached result.

The candidate is explicit `-RaftSimCachedCrestPublication` only. Ordinary
gameplay retains its existing publisher. A separate paired diagnostic advances
the candidate from startup and compares every output index and cell offset on
every publication. It does not compare screenshots or establish visual quality.

Editor build succeeds (119.04 seconds); five native D3D12 tests pass with the
candidate enabled: new publication cache, existing topology publication,
shoreline target cache, moving-bank cache and fine crests. Fixtures include
empty geometry, large arrays, changing signed index bits with identical owners,
changed/unsorted ownership, changed offsets, caller-discarded output and reset.
Fourteen strict parser tests pass; incomplete, duplicate, reordered, malformed,
nonexact, nonfinite, empty-workload and incorrect-order evidence is rejected.
The existing compiler warnings in unrelated detail/Chaos tests remain.

## Actual normal-game pairs

Two independent editor-hosted D3D12 normal-start runs each retain all 128 pairs
from frames 120 through 247. A publishes reference, B publishes candidate.
Order alternates in two-frame blocks. Timings include full cache comparison,
miss rebuild, key retention, allocation and copying, not just cache hits.
All 256 pairs preserve every index and offset exactly.

| Run / candidate first | Pairs / reused | Reference mean ms | Candidate mean ms | Slower pairs |
| --- | --- | --- | --- | --- |
| A / no | 64 / 45 | 0.218194 | 0.152805 | 19 |
| A / yes | 64 / 43 | 0.199361 | 0.186303 | 25 |
| B / no | 64 / 44 | 0.234674 | 0.157777 | 19 |
| B / yes | 64 / 43 | 0.209600 | 0.177695 | 21 |

This small component improvement does not demonstrate a whole-frame gain.
All rows and evidence hashes are in [qualification](crest-publication-cache/qualification.json).

## Ordinary cost: default promotion rejected

Four sequential same-binary 900-frame runs use reference/candidate/candidate/
reference. All use the **normal scenario start**, no review-station override,
1280x720, four solver lanes, ephemeral profile, no cook, paired audit, screenshots
or concurrent engine/build job. Rows 60..840 inclusive are retained; modern CSV
timing is confirmed in every process receipt, scope offset 1. These are short
first-pool samples, NOT the earlier rapid-at-8330 workload or full-river traversal.
Do not attribute their different absolute costs to this optimization.

| Run / path | FPS | Mean frame ms | p95 ms | Short-window 30 FPS p95 gate |
| --- | --- | --- | --- | --- |
| A / reference | 42.263270 | 23.661208 | 32.3236 | pass |
| B / candidate | 38.504365 | 25.971082 | 35.6647 | fail |
| C / candidate | 42.523842 | 23.516219 | 31.6105 | pass |
| D / reference | 42.474237 | 23.543684 | 31.7511 | pass |

B is worse than both controls; C is slightly better. The gain is not repeatable,
so **default promotion is rejected**. These runs do not establish causation for
the slower run, and successful short first-pool windows do not supersede the
unresolved rapid/whole-river 30 FPS requirement. Do not rerun this unchanged
candidate seeking a pass. No standalone game target or packaged traversal is
claimed by this editor-hosted investigation.

## Retained normal path checked

The final normal-start editor-hosted game exits 0 with no candidate or audit
override. Its [process receipt](crest-publication-cache/normal-process.json)
contains 24 captured 1280x720 views and a finalized 15.482-second recording.
All 464 encoded frames decode, with 28 exact adjacent repeats; the
[decode receipt](crest-publication-cache/normal-motion.json) retains original
frame hashes. Recording frame rate is not game FPS. Inspected actual capture
indices 12 and 22 show the raft/crew and flowing-looking first-pool surface;
broad smooth water, coarse repeated canopy and crew shading remain unaccepted.
No new visual improvement or full-route animation, shoreline or collision
acceptance is claimed. No engine, cook or source-audit process remains live.

Captured sources, terrain/collision, installed 4950-second fields and nonlinear
gameplay OFF remain unchanged. Completed scientific audits were not restarted.
The next work remains substantial water/geometry/physics integration and
full-route validation; this micro-optimization does not unblock conservative
front forces, open-boundary energy closure or realistic breaking water.
