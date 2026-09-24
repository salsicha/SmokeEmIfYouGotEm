# Deferred water-sample normals

2026-09-24. Scoped removal of overwritten work; not 30 FPS or visual acceptance.

Both the live-field and shared-atlas samplers computed a central-difference
normal before wet/dry reconstruction. `ResolveMixed` completely replaces that
normal whenever any available corner has exactly zero depth, including an
entirely dry footprint. The samplers now compute the original central normal
only when reconstruction declines the footprint. Interpolation, depth/bed,
wetness, velocities, coordinate conventions and solver state are unchanged.
`-RaftSimEagerSampleNormals` retains the original evaluation order in the same
binary for comparison. No extra threading or retained water values were added.

Editor build passed in17.90s. Native report
`tmp/deferred-sample-normal-native-20260924/index.json` records5successes,
0warnings/failures: WaterDryRockSampling, AtlasStencil, SharedCartesianAtlas,
CartesianPresentationSource and CartesianCropBoundaries. The extended dry-rock
test checks normal replacement for all16corner masks at9query positions.
These are scoped sampling checks, not full-scene geometric validation.

## Actual normal-start comparison

Same editor binary, normal FullReach scenario,1280x720D3D12offscreen, default
four solver lanes, unchanged physics/quality, no cook or concurrent diagnostics.
Execution order was control-a, candidate-a, candidate-b, control-b. All4runs
exited0 without timeout and confirmed nonlegacy CSV frame timing. The same
predeclared rows60..840(781rows) and offset1 were audited for every900row run.

| Run | Mean frame ms | p95 frame ms | Active source-sampling mean ms |
| --- | ---: | ---: | ---: |
| Control a |37.881847|45.3488|2.926764|
| Candidate a |30.910323|40.5633|2.672212|
| Candidate b |29.331910|39.6572|2.622182|
| Control b |29.324496|39.8652|2.759782|

Report: `tmp/deferred-sample-normal-abba-20260924.json`, including all CSV
hashes and full scoped measurements. Logs/CSVs use the prefix
`south-fork-deferred-normal-` under `unreal/Saved`.

Source sampling is lower in both pairs; the reverse whole-frame mean is
effectively unchanged and slightly worse for the candidate. Therefore the
large forward whole-frame gain is NOT attributed to this edit. All4p95values
FAIL the unchanged33.333333ms target. Retain this exact-work reduction, but do
not claim a general FPS fix, full-route stability, visual delivery or release
acceptance. Game rebuild session95464passed42.27s. Code-only staging is being
started at `tmp/standalone-stage-deferred-normal-v7-20260924` using the prior
cooked content; actual packaged verification remains required. This does not
include or validate the separate uncooked MetaHuman dependency restoration.
The existing v6package is preserved unchanged.

Staging session56526completed successfully (UAT157.68s, exit0). A fresh60-case
packaged regression is now running; no packaged or rendered acceptance yet.
The regression completed:57/60pass, all60finite/stable; the same3Troublemaker
timing gates fail (10.9558/11.1186/13.1526ms versus1.6ms). Actual packaged
normal-start rendering is being checked next. This is not full regression success.

## Packaged follow-through (terminal)

V7 normal-start render capture exited0 and produced12frames under the staged
game's `Saved/Screenshots/staged-v7-normal-start-20260924_000..011.png`.
Inspected002and011: crew, raft, terrain and water render; positions and water
patterns change. The early frame has visible temporal speckling; the later
frame is cleaner. Smooth/rippled water does not establish convincing crests or
froth. These bank-facing views do not validate faces, full-route collision,
shoreline continuity, or menu navigation. No visual improvement is claimed
from this mathematically equivalent sampling optimization.

A separate no-capture900frame run of the actual v7 executable exited0.
`tmp/staged-v7-normal-start-frame-audit-20260924.json` records predeclared
rows60..840 (781samples), offset1, confirmed nonlegacy frame timing:
mean35.621072ms (28.0733FPS), p9544.1487ms. The unchanged33.333333ms target
still FAILS. Game-thread mean34.512071ms and surface Tick mean19.802229ms
remain dominant; overlapping scopes must not be summed. CSV SHA256:
`789d0cbd490246cfba43950ab5254e758fa089ef7e4047dbdfe8b68298cf628a`.
This direct FullReach scenario launch verifies the updated packaged code runs,
not the main-menu path or sustained full-river acceptance. No cook or other
diagnostic ran concurrently. South Fork remains the first unfinished river.

## Next bottleneck: current packaged crest reconstruction

Separate300frame v7 run with existing `-RaftSimWaterStageTimings` exited0.
No cook/game was live at entry, and no other diagnostic ran concurrently.
Log: `tmp/staged-v7-crest-stage-cost-20260924.log`, SHA256
`fec7833e155972f6f1a353c65aea4156e76a7a6687fa13dac72e9cce724788bc`.
This instrumented run is localization, NOT a replacement performance gate.
Engine frames60..240 contain181crest updates:

| State | Frames | Mean total ms | Selection ms | Targets ms |
| --- | ---: | ---: | ---: | ---: |
| Geometry reused |101|1.670759|0|0|
| Geometry reevaluated |80|9.398533|3.840645|2.149434|

All80reevaluations record changed XY; none record changed source indices,
profile, coarse or shore arrays; one records changed detail window. This does
NOT imply unchanged adaptive selection masks or permission to reuse stale XY.
Within reevaluated selection, measured sample cost averages0.734994ms,
assembly2.413793ms and refinement input0.198830ms (other selection overhead
remains). Across181updates, midpoint expansion averages0.21ms and correction
history0.77ms, so midpoint scheduling is not the leading candidate.

Source inspection confirms exact per-level selection-mask reuse already exists
in `RaftSimSurfaceRefinement.h`; a root-index-only topology cache would be wrong.
Next inspect ordered edge insertion and triangle emission on changed masks,
including current indexed-edge lookup behavior and existing rejected trials,
before implementing an exact assembly improvement. Keep current-coordinate
sampling, 2cm crest error and all shoreline/physics gates unchanged. No new
playable visual improvement was delivered by this diagnostic run.
