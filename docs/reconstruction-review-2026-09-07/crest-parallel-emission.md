# Ordered parallel crest emission — September 24

REJECTED after whole-frame evaluation, not river acceptance. Normal staged game
is unchanged. Candidate code, opt-ins and temporary fixture were removed.

Existing topology reuse already requires identical root indices and every
selection mask. Do not reuse stale moving-shore coordinates. Instead this
candidate parallelizes triangle emission after the original serial edge-ID
discovery. It records each triangle's three existing midpoint IDs, computes
ordered output offsets, then writes disjoint output ranges in parallel. The
original winding, child order, midpoint parent order and cell origins remain
unchanged. No selection tolerance, crest height, geometry density, hydraulic
state, interpolation clock or shoreline criterion changes.

During evaluation the candidate flag was `RaftSimParallelCrestEmission`; the
default stayed serial. Same-input comparison used `RaftSimCrestEmissionComparison` with the existing
`RaftSimCrestIndexedEdgeAudit=PATH` harness. Its report identifies
`serial_vs_parallel_emission_both_indexed`; legacy timing labels mean reference
and indexed labels mean candidate in this explicit comparison mode. Both use
the installed indexed edge map and the same current range predicate.

Editor build succeeded in 146.92s; existing two D6 Chaos double-to-float
warnings remain. Native `RaftSim.WaterDetail.RefinementEmission` and
`RaftSim.WaterDetail.RefinementTopologyCache`: 2 successes, 0 warnings/failures,
`tmp/crest-emission-native-20260924/index.json`. The new fixture compares 24
moving-profile/coordinate, crop, dimension and winding states, including exact
ordered parents/triangles/owners, expanded coordinates and build/reuse counts.

Actual default Boot/menu-handler/FullReach comparison completed 900 post-travel
frames and exited 0. All 64 pairs after two warm builds preserve ordered
parents, triangles, owners, expanded current coordinates and production
topology exactly. Report `tmp/crest-emission-live-pairs-20260924.json` and
matching `.log`; no concurrent cook/build/test. Timings include temporary
allocation, midpoint lookup, prefix construction and output publication.

| First path | Pairs | Reference build ms | Candidate build ms | Reference assembly ms | Candidate assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reference | 32 | 2.435713 | 1.855206 | 1.652610 | 1.104003 |
| Candidate | 32 | 2.522471 | 1.895807 | 1.739663 | 1.103288 |

This is component evidence, not uninstrumented FPS, rendered motion,
collision/shoreline acceptance or a new visible water improvement. The separate
control/candidate/candidate/control whole-frame decision follows below.

## Whole-frame decision

Same editor Game binary, default Boot/menu-handler/FullReach, ephemeral profile,
1280x720 D3D12, NVIDIA RTX 3060 laptop adapter 0. No concurrent cook/build/test.
900 post-travel frames per run, strict unchanged audit rows 60..840 (781),
confirmed nonlegacy timing offset 1. Each run exits 0.

| Run | Mean frame ms | p95 ms |
| --- | ---: | ---: |
| Control a | 32.601429 | 41.8021 |
| Candidate a | 35.639640 | 45.0277 |
| Candidate b | 34.637855 | 42.8120 |
| Control b | 35.203842 | 42.4520 |

Reports `tmp/crest-emission-{control-a,candidate-a,candidate-b,control-b}-20260924.json`
contain exact raw CSV paths and hashes; corresponding `.log` files record
launch and completion. All four fail 33.333333ms. The first pair loses in mean
and p95; the reverse pair improves mean slightly but worsens p95. This does not
establish repeatable whole-frame benefit or a causal regression. Do not promote
the candidate from the component timings or repeat it unchanged.

The three existing source files were restored without reverting unrelated
work; the two new candidate-only files were removed. Native/report evidence is
retained here. The staged Game never contained this experiment, so no staged
rollback or hydraulic re-cook is needed. No new visible water improvement,
geometry correction or river acceptance is claimed.

Restoration editor build is terminal SUCCESS, 145.63s:
`tmp/crest-emission-restoration-build-20260924.log`. Git shows zero remaining
diff in all three modified existing source files. Live-pair report SHA256:
`0ed2bc8194fe56278ba2006e0d2dba0ca28ad748b3b0152338ba04cd8e112095`.
The unchanged installed Game SHA256 is
`394d06c94b22918ba83afac9a3831991d76229dac5ba955acdfcfea7b486726e`.

Restoration editor build is terminal SUCCESS, 145.63s:
`tmp/crest-emission-restoration-build-20260924.log`. Git shows zero remaining
diff in all three modified existing source files. Live-pair report SHA256:
`0ed2bc8194fe56278ba2006e0d2dba0ca28ad748b3b0152338ba04cd8e112095`.
The unchanged installed Game SHA256 is
`394d06c94b22918ba83afac9a3831991d76229dac5ba955acdfcfea7b486726e`.
