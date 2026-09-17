# Crest normal-work comparison and qualification recovery

Recorded 2026-09-17 UTC. The normal-pass candidate was rejected and removed
from production. This is useful measured evidence and regression coverage,
not a new water feature or a 30 FPS pass.

## Exact candidate, insufficient speedup

The candidate skipped a face-normal calculation only when none of its three
vertices consumed a recomputed normal. All incident faces of touched vertices
remained, including all-coarse triangles sharing a touched corner. It changed
no positions, indices, winding, attributes, normal sums or geometry selection.

Seven native D3D12 tests passed with the candidate enabled. The first NullRHI
attempt was 6 pass / 1 fail because ShorelineFineCrest requires an actual
rendering proxy; that report remains a failure, not a waived assertion.

All 64 actual South Fork pairs on frames 120-183 preserve every compared
attribute (4,302,641 vertices). The two independently retained incidence caches
see the same successive inputs, including rebuilds, with alternating call order.
Vertex copies and comparisons are outside the measured scopes.

| Call order | Original mean ms | Candidate mean ms | Candidate faster |
| --- | ---: | ---: | ---: |
| All | 0.994836 | 0.954973 | 36/64 |
| Original first | 1.095590 | 0.991368 | 28/32 |
| Candidate first | 0.894081 | 0.918578 | 8/32 |

The candidate is slower when called first, so it fails the unchanged
both-orders promotion gate. The runtime branch and audit hook were removed,
not left as another unused option. Original runtime normal code is unchanged.
The rejected sources remain in ignored
`tmp/crest-unused-face-v1-20260917/RejectedSources/`, with its isolated DLL.
The strict log auditor and negative tests remain available to reproduce the
rejection from retained evidence.

Pair report: `tmp/south-fork-crest-unused-face-pair-v1-20260917.json`, SHA-256
`594ce3903102cffbffbb5b7d18598990fa5260f834159d94ce1eb724bac05fa6`.
Source log SHA-256:
`48a2e34897e6b7d9884ff3ffa79ab695aa382276fe8b19df44c8076a737345d4`.
The ordinary 30 FPS gate was not run for this rejected candidate.

The capture explicitly paused/resumed the original hydraulic process, SM5
editor/remaining workers, and standalone compiler through retained handles.
All resume statuses are zero, all 63 frozen shader hashes remained unchanged,
and all original jobs resumed. The profiler now accepts an exactly quoted
`"-sm5"` token as well as the unquoted token, while retaining the other exact
PID/start/executable/parent/command-line identity checks. Ten tests reject
wrong versions, suffixes and unbalanced quotes.

The normal regression now additionally covers no refined vertices and all
refined vertices. The final restored runtime with those tests compiles/links
and passes all seven native D3D12 tests, no warnings/skips in the test report:
`tmp/crest-normal-extremes-native-v1-20260917/index.json`, SHA-256
`5cf736f147d50e8729fe2096b84eb6104147b1dec9f178f7decfa28ca3766675`.
An existing C4701 compiler warning in DetailSourceFootprint remains; this is
not a warning-clean build. Forty Python audit/profiler/frame-CSV checks pass:
`tmp/crest-normal-rejection-tests-v1-20260917.xml`.

## Larger performance cost still open

The existing ordinary capture remains 28.057157 FPS / p95 41.2354 ms (FAIL).
Its normal pass averages 0.567391 ms; adaptive selection averages 3.602291 ms
overall, 7.326008 ms on the 89 active frames, p95 10.5898 ms. Across the
181-frame window, XY and profile change 88 times each, root indices twice,
detail window once; 231 topology levels reuse assembly and 36 rebuild it.
Thus repeated current-profile selection, not only triangle assembly, remains
a larger target. Do not freeze evolving profiles, lower detail or weaken the
independent shape-error gate to improve timings.

## Transport configuration correction and live work

The fresh transport build in session 60207 is terminal. It compiled model
version 1 while its original unscaled fixture has header version 3. This was
a launch-configuration mistake. The phase tags and original force/geometry
oracles correctly rejected it: **50 pass / 4 fail** in 122.25 seconds.
Report: `tmp/sm5-production-correction-regression-v1-20260917.xml`.
This does not supersede the earlier correctly configured 54 passing checks.
The fixture, expected outputs and acceptance gates are unchanged.

A corrected build derives the model version directly from the original binary
header. Session **26355 / PID 37212**, start UTC
`2026-09-17T04:40:04.6241104Z`, version 3, 18 cases, is live at phase 3.
Witness: `tmp/sm5-transport-production-unscaled-v2-20260917-process.json`.
Its original handle queues the combined 54-test suite after compilation;
expected report: `tmp/sm5-production-unscaled-regression-v2-20260917.xml`.
Do not restart on an observation timeout.

Native 33-test SM5 replay **55459 / PID 36412** is still live with all 63
shader inputs frozen. Its current inputs already select the original unscaled
fixture; the standalone launch mistake did not change the native replay.

Same hydraulic PID 36872: 2,050-second state and all 86,720 exact-dry bank
checks pass. Depth max 4.321654 m, speed max 7.268524 m/s, volume
2,984,629.058002 m3, maximum step conservation residual 1.515815e-8 m3.
Outflow 95.712019 versus inflow 45.306955 m3/s: still not settled, no snapshot
promotion. Reports are `tmp/control-ablation-2050s-state-v1-20260917.json` and
`tmp/control-ablation-2050s-banks-v1-20260917.json`. Next complete
2,100-second/local 6,000 snapshot needs both audits.

All remaining physical water/visible waves/froth, terrain/boulders/collision,
safe installed play, 30 FPS, later rivers, crew, normalization and release
requirements remain open. Troublemaker remains a rapid within South Fork.
