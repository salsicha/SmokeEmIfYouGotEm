# Healthy packaged South Fork rapid check — September 26

The repaired playable build keeps water detail running at station 11,520 m,
but this rapid **fails the 20 FPS budget**. This is validation and diagnosis,
not a new visible delivery or geographic/hydraulic acceptance. South Fork
remains first in the reconstruction queue.

## Reproduction and limits

Run `unreal/Scripts/profile_south_fork_menu_launch_ps5.ps1` with
`-Label sf-v4-healthy-rapid11520-20260926 -ProfileFrames 1200
-ReviewStationM 11520 -PackagedRoot
C:/Users/salsi/repos/SmokeEmIfYouGotEm/tmp/south-fork-playable-v4-20260926/Windows`.

This uses the rebuilt standalone game and normal quality/physics, but launches
the FullReach review station directly. It is not a Boot/menu traversal or a
full-route test. No other engine/build/cook process ran during measurement.
The previous [normal-menu validation](south-fork-entrainment-roundoff.md)
remains the normal-launch evidence; do not substitute this diagnostic for it.

Binary SHA256:
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.
CSV SHA256:
`d2202b769a062bf0de86552abb65a84f6a270778aed0309af61fcfb2c1cad706`.
Saved [receipt](south-fork-healthy-rapid11520/frame-audit.json),
[CSV](south-fork-healthy-rapid11520/frames.csv) and
[runtime log](south-fork-healthy-rapid11520/profile.log).

## Timing and health

Of 1,200 frames, the unchanged audit window is rows 30 through 1169 (1,140
frames). Mean 59.8223 ms; p95 **85.2731 ms**; maximum **141.7508 ms**;
**17 individual frames exceed 100 ms**. Maximum consecutive pair 264.0579 ms
is retained as additional diagnostic information, not a replacement criterion.
The agreed gates remain p95 <=50 ms and no individual frame >100 ms.

Exit code 0, zero logged runtime errors, 1,199 paired presentation commits,
1,202 rendered-frame detail snapshots, and zero detail-clock backlog after
72.6543 wall seconds. The startup detail shutdown did not recur.

The cost is not solely startup: rows 800 through 1169 alone have mean
46.597 ms and p95 56.5818 ms, still over budget. This late slice is diagnostic
only; the failed primary audit window is not shortened to obtain a pass.

## CPU cost breakdown

Selected CSV scope means over the same 1,140 frames:

| Scope | Mean ms |
| --- | ---: |
| Game thread | 57.731 |
| Surface tick | 34.609 |
| Cartesian publish | 18.037 |
| Shoreline SetMesh | 16.581 |
| Surface refresh | 15.903 |
| Crest update | 14.281 |
| Solver StepWater | 13.702 |
| Crest selection | 8.490 |
| GPU | 18.512 |

Scopes are nested: **do not add these means as independent costs**. This run
is principally CPU-limited. Crest updates average 1.0009 per frame, so repeated
multiple crest publications per frame are not established as the cause.
XY/profile changes occur in about 69.1% of frames; root-index changes in 1.4%.
Topology levels built/reused average 1.6465/0.4298 per frame.

The generic `audit_unreal_frame_csv.py` rejects this CSV because the engine
emits the unrelated header `NumInstanceTransformUpdates` twice. The breakdown
above used a read-only extraction from the final `EVENTS` footer header,
requiring each selected scope name to appear exactly once and have a value
in every selected row. No duplicate scope was used, no parser gate was
relaxed, and the packaged profiler's frame receipt remains authoritative.

### Reproducible workload analysis follow-up

The parser now has an explicit `--ignore-duplicate-unmeasured-header` option.
Default duplicate rejection is unchanged. The option cannot exempt any measured
frame/thread/GPU/water scope, does not select either duplicate's values, and
records the original column indices. Unknown additional duplicates, changed
metric positions, truncated rows, missing footers and absent named exceptions
still fail. Seventeen parser/workload tests pass. The local UE5.8 engine source
registers `NumInstanceTransformUpdates` in both
`Engine/Private/InstanceData/InstanceDataManager.cpp:741` and
`Engine/Private/InstancedStaticMesh/ISMInstanceDataManager.cpp:685`.

The retained CSV was reanalyzed without launching another game. Reproduction:

```text
python physics/scripts/audit_unreal_frame_csv.py
  docs/reconstruction-review-2026-09-07/south-fork-healthy-rapid11520/frames.csv
  --first-sample 30 --last-sample 1169 --target-fps 20 --require-water-scopes
  --frame-time-scope-offset 1
  --ignore-duplicate-unmeasured-header NumInstanceTransformUpdates
  --report <new-output-path>
```

The [reproducible report](south-fork-healthy-rapid11520/workload.json) retains the
original CSV hash, 1,140 samples and failed p95 85.2731 ms unchanged. It records
the ignored unmeasured counter at columns 228 and 230. Timing phase 1 is justified
by `csv.UseLegacyFrameTime = "false"` in the retained runtime log, not selected
to improve correlations. Each elapsed interval is associated with the preceding
logical frame's scopes:

| Refresh / crest selection | Frames | Mean frame ms | p95 ms | Frames >50 ms |
| --- | ---: | ---: | ---: | ---: |
| No / yes | 352 | 46.45 | 53.53 | 69 |
| Yes / no | 350 | 49.59 | 56.59 | 165 |
| Yes / yes | 438 | 78.75 | 94.65 | 438 |

All 1,140 samples remain; none has both timings zero. Overlapping refresh and
selection is associated with the largest costs, but both single-work groups
also exceed the p95 target. This is not proof of causality or authorization to
skip either work item or change cadence. The follow-up fixes a diagnostic
compatibility problem only; no new game build, visible improvement, performance
pass, source acquisition or river acceptance is claimed. The single-insertion,
parallel-emission and sparse-root candidates were checked against their prior
rejection records and were not rerun or reintroduced.

Earlier editor/host measurements are not a controlled before/after comparison
with this run. Do not attribute the timing difference to the roundoff repair
without matched measurements.

## Actual rendered motion

A separate same-binary capture used
`RaftSim.CaptureRaftSeries 12 10 0.5 sf-v4-rapid11520-motion-20260926 7 2 3 6 paddle`
at the same review station. Ten frames show raft/paddle pose changes and travel
relative to the banks. Detail remained healthy: 127 preparations over 19.864 s,
zero backlog, no logged runtime errors. Retained [motion log](south-fork-healthy-rapid11520/motion.log),
[first frame](south-fork-healthy-rapid11520/motion-first.png) and
[last frame](south-fork-healthy-rapid11520/motion-last.png).

No obvious open water seam or gross raft/bank penetration is visible in this
short view. That is not a collision or shoreline-stability acceptance test.
The rapid still reads as broadly smooth water with specular ripples rather
than a convincing breaking wave train. Geometry/whitewater fidelity remains
open; no new measured boulders or underwater geometry were introduced here.

## Next bounded work

Target exact-preserving CPU work in surface publication/crest selection and
validate a new candidate against this healthy packaged baseline, including
both timing and rendered motion. Do not enable the previously rejected
retained-capacity, empty-tile or inline-selection experiments, reduce geometry
tolerance/cadence, or disable water detail to obtain a pass. Separately retain
the geometry, collision, shoreline and rapid-wave acceptance gates. No cook,
source acquisition or Colorado promotion is justified by this check.
