# Root-edge incidence cache — September 26

Rejected after identical-input live timing. The candidate preserved geometry,
but did not improve whole adaptive-build time in both execution orders. It
was never enabled in ordinary play or installed in the packaged game. Do not
repeat this unchanged candidate in search of a passing timing result.

## Distinct hypothesis and invariants

The first refinement level usually retains root connectivity while shoreline
coordinates and selection masks change. The candidate cached each root
triangle's outgoing-edge slot, sharing slots for reversed/common edges. It
reset every midpoint ID on each preparation and retained original serial edge
discovery, parent orientation, triangle emission and ownership order. Higher
levels used the existing indexed edge map. Coordinates, sampled profile
values, refinement tolerance, levels, physics and publication cadence did not
change. This was not the previously rejected single-lookup, parallel-emission
or sparse-root-selection experiment.

The temporary candidate switch was `RaftSimCachedCrestRootEdges`; comparison
used `RaftSimCrestRootEdgesAudit=PATH`. Both were off in normal play. The
comparison includes root incidence construction, validation and per-build
reset, not just the cheapest lookup loop.

## Native and actual-game results

The first editor build failed on an unavailable `TIsSame` trait and concurrent
incomplete Hance source edits. Replacing that trait with standard C++
`std::is_same_v<std::decay_t<...>, ...>` and rebuilding after the shared edits
settled passed in 405.28 seconds. No failed build is counted as a pass.

Native NullRHI: 2 successes, 0 failures/not-run tests, engine exit 0.
`RaftSim.M4.CrestRootEdges` compared 22,361 expanded vertices across 32
changing-coordinate/profile/grid-size/winding/detail/level states, with explicit
invalidation, high-degree overflow, reversed and degenerate shared edges and
midpoint reset checks. The existing
`RaftSim.WaterDetail.RefinementTopologyCache` also passed (38,416 vertices).
See [native log](crest-root-incidence-rejected/native.log).

Actual editor-hosted FullReach at station 11,520 m, D3D12, 1280x720,
ephemeral profile, 350 frames, no concurrent build/game during measurement.
This direct review-station launch is not normal-menu or packaged acceptance.
After two warm builds, all 64 alternating-order pairs preserve exact ordered
parents, triangles, owners, expanded current coordinates, build/reuse counters
and production topology. Engine exit 0; no logged runtime error. The
instrumented frame timing is not an ordinary FPS measurement.

| Candidate first | Pairs | Reference build ms | Candidate build ms | Reference assembly ms | Candidate assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| No | 32 | 12.616778 | 12.728322 | 4.213212 | 4.165657 |
| Yes | 32 | 13.376003 | 13.014288 | 4.266775 | 4.265228 |

One whole-build order is slower, so the repeatable-speed gate fails. Mean
retained topology storage also increases from 3,455,499 to 4,283,366 bytes.
No second capture, whole-frame promotion trial, recook or package rebuild is
justified after this rejection.

The [pair report](crest-root-incidence-rejected/rapid-pairs.json) has SHA256
`13947c7368cedcae41af5858d7383a4cb548d2daf83589163358e9339a71f8c0`;
[live log](crest-root-incidence-rejected/rapid.log). The bounded launch helper
and build/native receipts remain under `tmp/crest-root-edges-*20260926*`.

## Removal and remaining work

The candidate field/branch, helper, native fixture and live audit were removed.
The two existing runtime files match the turn's starting revision `c9637b5a0`.
A concurrent shared commit `e8b1a7075` captured the experimental source before
removal; it remains recoverable there. This scoped removal does not revert
that commit's unrelated Hance work or delete any captured river data.

The installed v4 executable remains SHA256
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.
No new visible improvement, lower frame time, motion/collision/shoreline
acceptance or river completion is claimed. South Fork stays first and its
healthy packaged rapid failure remains authoritative. Further optimization
needs a different hypothesis; do not substitute disabled detail or reduced
geometry/physics quality for the 20 FPS requirement.

Restoration editor build is terminal SUCCESS, 456.23 seconds; log retained at
`tmp/crest-root-edges-restoration-build-20260926.log`. A post-removal native
recheck was not launched: the process guard found shared engine work (observed
`UnrealEditor-Cmd` PID 24432). Neither blocked launch created a test log or ran
assertions. The two earlier candidate-era native passes above remain valid,
but are not relabeled as post-removal results. Once the shared engine is idle,
run `RaftSim.WaterDetail.ConformingSurfaceRefinement` and
`RaftSim.WaterDetail.RefinementTopologyCache`; no further candidate experiment
is pending. No other session's process was stopped.

Repository write access is now explicitly granted and the scoped removal
succeeded. No OS ACL, ownership or security-setting change was made.

### Deferred restoration regression completed (September 26, 23:02 UTC)

After the shared engine exited, the two post-removal native regressions ran
against the rebuilt editor using NullRHI and `/Engine/Maps/Entry`. Both exact
test paths listed above succeeded: 2 successes, 0 failures, 0 not-run tests;
engine exit 0. The topology-cache test compared 38,416 current vertices, with
25 cached builds, 33 reuses and 58 fresh builds. Receipt and raw log:
`tmp/crest-root-edges-restored-native-20260926/index.json` and
`tmp/crest-root-edges-restored-native-20260926.log`.

This closes the deferred restoration check only. NullRHI is not a rendered
view, normal playable launch, motion/collision acceptance or a frame-time
measurement. No candidate was restored or enabled, and the packaged rapid
performance failure remains open. No other session's engine was stopped.
