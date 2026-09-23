# South Fork water-shadow filtering qualification

Reviewed 2026-09-23 UTC. Supporting qualification, **not a visible delivery**.
Default promotion is rejected for this trial; normal rendering stays unchanged.

This completes the shadow-preserving follow-through to the
[raft-edge discrimination](raft-edge-shadow-review.md), without repeating the
invalid ECVF_Cheat control or filling already-wet geometry. The local UE5.8
renderer has SingleLayerWater DepthPrepass enabled by default. Filtering needs
both read-only shader support and its runtime switch; enabling only the latter
does not establish the intended path. The process-local candidate requested:

```
-ini:Engine:[/Script/Engine.RendererSettings]:r.Water.SingleLayer.ShadersSupportVSMFiltering=1
-DPCVars=r.Water.SingleLayer.VSMFiltering=1
```

All five game logs confirm the requested values. This verifies accepted config,
not execution of a particular GPU pass; no GPU capture establishes that yet.
No project config, map, material, geometry, collision or field was changed.

## Actual motion and visual result

The installed FullReach/full_descent map used explicit8330 m review placement,
four solver lanes and D3D12 at1280×720. This is not normal scenario start or
reconstructed hull-clearance acceptance. The guarded capture exited0 and
retained24 screenshots, final carrier/camera data and a movie. All466 movie
frames decode, PTS0–15.5 s,18 adjacent exact repeats. Encoding rate is not FPS.
Original final screenshot and decoded6/13 s views were inspected. Cast shadows
remain, including the gray patch beside the left paddle/raft. There is no
convincing visible correction. Broad smooth foam, angular rocks, repeated canopy
and crew-fit limitations persist. Camera/raft states differ from prior captures;
this is not a registered same-state pixel comparison.

Motion: `unreal/Saved/VideoCaptures/RaftSim_20260923-133536.mp4`.
Decode: `tmp/water-shadow-filter-motion-v1-20260923/report.json`.
Final still: `unreal/Saved/Screenshots/south-fork-water-shadow-filter-v1-20260923_023.png`.

## Independent ordinary cost captures

ABBA captures each retained900 frames, analyzed over zero-based rows60–840
inclusive (781 samples),30 FPS target. Modern FrameTime mode is log-confirmed;
water scopes use preceding-row offset1. No motion/screenshot/optical override or
shadow disabling occurred in these cost runs. Shader support was1 in ALL runs;
only runtime filtering varied0/1/1/0. Thus controls are matched-compile controls,
not the unmodified shader-support0 project default.

| Run | Runtime filtering | Mean frame ms | p95 ms | p95≤33.333333 ms |
| --- | ---: | ---: | ---: | --- |
| A |0|27.280441|38.0804|FAIL|
| B |1|28.729833|39.8348|FAIL|
| C |1|24.530945|33.5328|FAIL|
| D |0|24.224985|32.9872|PASS|

Candidate B is slower than adjacent A; candidate C is slower than adjacent D.
Substantial between-pair variation prevents precise causal cost attribution.
Both candidate p95 values fail. One short control pass is not sustained or
whole-river performance acceptance. Report:
`tmp/water-shadow-filter-cost-v1-20260923.json`.

Session75358 and all five game processes are terminal exit0/no timeout. Every
capture reports successful guarded suspension/resumption of original cook36692,
and the same normal solver archive63e9e592…f1d0365f. Fresh process inventory finds
only that cook live; no duplicate was launched. Frame-audit explanatory text
now makes Refresh's possible nested CartesianPublish explicit; calculations and
gates are unchanged. All13 existing parser regressions pass.

## Next boundary

Do not promote or repeat this unchanged filtering trial. Any further claim that
filtering fixes the patch needs a registered state comparison and evidence that
the intended GPU projection actually runs. The existing wet-carrier evidence
still argues against geometry hole-filling at the sampled pixels. Continue
bounded playable reconstruction work; this diagnostic does not close any river.
Installed4950 fields and nonlinear OFF remain unchanged. South Fork precedes
Colorado, Pacuare and Futaleufu, all still unfinished.

The [retained receipt](water-shadow-filter-review.json) binds23 artifacts,
including process/log/CSV/motion/tests and both new15500/15550 checkpoint audits.
