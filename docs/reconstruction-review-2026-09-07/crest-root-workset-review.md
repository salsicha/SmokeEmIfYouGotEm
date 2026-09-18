# Sparse crest-root workset rejected in actual gameplay

2026-09-17. The candidate committed in `5d4e8730b` is removed after its
actual-game comparison. It was never enabled by default. That commit preserves
the implementation, fixture and diagnostic for recovery; no generated build,
recording or report needs to enter Git. Normal geometry and quality are unchanged.

## Why this trial was tested

The preceding stage-timing capture, `south-fork-publication-cost-v1-20260917`,
shows 61 rebuild and 120 non-rebuild observations over engine frames 60–240.
Rebuilds average 9.346882 ms, including selection 5.509010 ms and targets
0.774020 ms; non-rebuild updates average 2.814065 ms. All 61 rebuilds have BOTH
changed XY and changed profile. Retaining the preceding full selection or old
height samples would therefore be incorrect. These are diagnostic CPU scopes,
not additive whole-frame timings or an FPS qualification.

The trial excludes roots provably outside current crest support and the detail
window from adaptive work, retaining a conservative neighbour ring. It merges
every omitted original triangle back into the full ordered output. No rendered
triangle, contact surface, tolerance, physics rate or source data is reduced.

## Evidence and rejection

The candidate editor build succeeds. Eight native checks pass under NullRHI;
the ninth, ShorelineFineCrest, requires a non-null rendering proxy and fails
there, then passes with D3D12. The new fixture compares changing support,
topology, winding, geographic orientation and coordinates over 18 frames.
Reports are `tmp/crest-root-workset-commit-{native,renderer}-v1-20260917/`.

Actual FullReach gameplay, review station 8330, compares 16 alternating
changed-input pairs after two warmups. Every pair preserves exact ordered
midpoint parents, complete triangle topology, original ownership and expanded
coordinates, also matching production topology. The diagnostic arrays are
never published. Retained roots fall from 16,488–16,490 to 8,101–9,092, but
**every pair is slower**, including pruning and full-output merge:

| Execution order | Pairs | Reference mean ms | Candidate mean ms |
| --- | ---: | ---: | ---: |
| Reference first | 8 | 5.676212 | 6.736600 |
| Candidate first | 8 | 6.536212 | 7.580800 |

The cost regression rejects the candidate before an audit-free whole-frame
performance or installed-contact trial. There is no justification to promote
it or to claim an FPS improvement from fewer working roots.

Report: `tmp/crest-root-workset-actual-a-v1-20260917.json`, SHA256
`06404e5dd6c2ebb2c56d2659464927be285806e50465102e8a77ed6edfa39b5f`.
Capture label: `south-fork-root-workset-a-v1-20260917`, 900 frames.
Process report confirms exit zero, no timeout, successful suspension/resumption
of the explicitly identified cook and unchanged cook CPU during capture.
CSV SHA256 `8d3f8e60d2404b8203d620950f7b98781581e60667bb29e4771c6f78d39c6445`;
this instrumented CSV is NOT an FPS acceptance run.

## Remaining acceptance

Removing the candidate restores the two existing runtime files byte-for-byte
to `127ef2a8f`; the three new candidate files are removed. The visible-carrier
spray correction remains installed. Restored editor Development build succeeds
(468.53 seconds), with the previously observed C4701/C4305 warnings. All ten
targeted native tests pass with D3D12, zero warnings/failures/not-run tests:
crest target/exact/moving-bank caches, fine crest, opposite dry fan, visible
spray carrier, source packing, committed foam evolution, conforming refinement
and topology cache. Report:
`tmp/crest-root-workset-restored-native-v1-20260917/index.json`, SHA256
`b1a1dcbf1927133b97978e099fa030d2ace486ecb38639e9df5ad2ea593b0812`.
No new visual, physical, motion or 30 FPS acceptance is
claimed. Do not repeat this support-pruning variant as a presumed speedup.

Final ordinary audit-free capture `south-fork-root-workset-restored-v1-20260917`
has 300 rows, 1280x720 D3D12. Fixed CSV sample rows 60–240 yield
34.854890 FPS but p95 38.0726 ms: **FAIL30**, whose budget is 33.333333 ms.
Report `tmp/crest-root-workset-restored-profile-v1-20260917.json`; CSV SHA256
`5b5c52ecf93ed459a6fa66b53edc875eafd152bf61120bc32bf275f698f70ed6`.
The process exits zero without timeout; cook suspension/resumption succeeds,
with observed cook CPU delta 0.125 seconds across that interval, not zero.
This is a fresh baseline, not a controlled improvement comparison with earlier
captures (some used rows 30–90). No packaged or sustained acceptance follows.

Physical varying-inlet/front coupling, consistent pressure/energy, breaking
and convincing froth remain open, as do sustained performance and the ordered
South Fork → Colorado → Pacuare → Futaleufu queue. Chilko/Zambezi, crew,
normalization, regressions and release remain required. Troublemaker remains
a rapid in South Fork, never a menu scenario.
