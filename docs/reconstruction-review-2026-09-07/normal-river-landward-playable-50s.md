# Landward rock with source-matched 50-second playable water

September 15, 2026. This completes the landward candidate's initial joint
playable comparison, NOT visual, settled-hydraulic, traversal or performance
acceptance. Troublemaker remains a rapid within the South Fork scenario.

## Same geometry, fresh water

The existing landward cook (session59493/PID24324) finished successfully:
1,000 steps of 0.05 seconds, with no restart or transfer of evolved old-bed water.
All 5,350,400 cells pass the retained snapshot gates. Maximum depth is
4.277083789 m, maximum speed 12.166877129 m/s, and maximum step conservation
residual 1.068264882e-8 cubic metres. All 86,720 artificial bank-face cells remain
exactly dry. This is not a settled-flow result: instantaneous boundary fluxes
remain unbalanced and the accumulated volume change is +955.595057 cubic metres.

Reports are `tmp/south-fork-landward-50s-{snapshot,banks}-v1-20260915.json`.
The original raw returns, selection interpretation, source cap and cold input
are unchanged from [the landward geometry record](normal-river-landward-source-extension.md).

Runtime export: `tmp/south-fork-landward-runtime-50s-v1-20260915`.
All 799 source packets and 836 atlas cores verify, including 41,987,038 exact
packet/atlas bed comparisons. Eight compound packets are rebuilt, 791 unchanged
packets are verified and reused. Atlas SHA256:
`9f05b2b40afbb4d27849776148f2e5a692cef3a73b5aba1777ef9720671a2b1c`.

Coverage retains all 406,823 original captured-water probes and the unchanged
8 m required raft margin (actual minimum 10 m). The same region_0002 physical
edge correction remains necessary; no missing sample is discarded. Repaired
streaming manifest SHA256:
`2c242bae42822138932b668f849905347a8e8f869aeece5123e5f81489830b11`.
Coverage report: `tmp/south-fork-landward-runtime-50s-coverage-v1-20260915.json`.

## Native proof and exact-state binding

Actual saved South Fork ground plus the transient candidate passes all 30,403
union probes at the existing 1 mm gate. All 12,800 native bed/depth/surface/flow
queries match this 50-second state. Maximum bed/surface error is 7.629395e-6 m;
depth 1.191917e-7 m; velocity below 2.0e-7 m/s. Zero wet-mask mismatches; the
solver's 1e-6 and native sample's 1e-4 depth thresholds remain distinct.

Native report:
`unreal/Saved/RaftSimValidation/south-fork-landward-runtime-50s-v1-20260915.json`,
SHA256 `d4418e180a69664f24589cfc853e3cb5edfd0b41eeb3e3682cb30e2e3af4c057`.
No solver steps run during this loader comparison. The prior isolated legacy
ray failures are NOT closed by this different actual-map-union test.

The native report now records atlas and packet hashes. Preview preparation
requires that native evidence match the selected initial packet, atlas, source
time, window center and geometry, with all original 12,800 queries and no
failures. Previously, a successful one-second pilot report could qualify a
later preview. Old reports without the additional evidence are rejected rather
than silently upgraded; old evidence files remain unchanged.

The 6,404-triangle source-exact mesh is staged at
`/Game/RaftSim/Environment/GeneratedLocalReview/JointLandward50s20260915/SM_OriginalReturnRockSolid`.
The original ground material and parent remain byte-identical, with the exact
registered world-UV translation and no material displacement. Only this
regenerable local-review mesh is saved; no production map or profile is changed.

Descriptor: `tmp/south-fork-landward-joint-preview-50s-v1-20260915.json`, SHA256
`1bebc0574e3b6a4eb945d02e2118f2b4e507ef3f816fe0bd68373e1692df5c74`.
It binds 3,256 dependencies, including the explicitly interpreted selection.

## Actual game and reference comparison

`landward-joint-preview-50s-source-v1-20260915` runs in the EXISTING South Fork
game with the normal raft and one water surface. The positive launcher report
verifies one matching installation before BeginPlay, the exact source time,
single-surface startup, three screenshots and a finalized recording. It does
not infer success merely from an engine exit code of zero.

Camera: world centimetres (-545095,-362309,1800), pitch -27.8, yaw 18.075,
FOV 90, 1280 by 720. Recording:
`unreal/Saved/VideoCaptures/RaftSim_20260915-163141.mp4`, SHA256
`0604f3e634b3692edf71ffb7511d650e52776debd2b06d9662fac0f6eeb6178a`.
All 186 encoded frames decode, representing 60 engine source frames across
6.214 seconds. Encoding at 30 Hz is NOT evidence of 30 FPS gameplay. The
original long cook was still running, so this capture is not a performance run.

Inspected the original first screenshot and the unmodified decoded 5-second
frame in `tmp/south-fork-landward-50s-motion-v1-20260915`. The raft advances
downstream and the water changes, but steep triangulated inferred flanks,
broad white froth, smooth green wave faces and unfinished distant terrain
remain plainly visible. This is not a visually accepted reconstruction.
The decoder's inherited named ROIs are wrong for this camera (its `foam_face`
rectangle covers rock); their statistics are NOT used for foam acceptance.

The public [Raft California reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
is accessible again. Viewed displayed frames during playback and paused at
0:30; this is not a claim to have watched or calibrated the entire clip.
The reference shows irregular localized breaking tongues, darker gaps and
angular exposed rocks. Lighting, viewpoint and water discharge are not matched.

The current water-material file still matches the exact restored baseline
SHA256 `44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`.
Its recorded graph uses the original advected clumps with whole-cell smoothing;
the previously rejected irregular/micro-normal experiments are not installed.
No foam amount, shader, normal or physical parameter was changed in this review.
NEXT distinguish local foam production from optical smoothing using the actual
current carrier fields; do not repeat rejected texture changes or infer fluid
velocity/foam coverage from unrelated screen rectangles.

## Presentation regressions and remaining work

The four previous presentation source-text failures referenced obsolete inline
map checks, array access and fixed route bounds. Tests now guard the exact
South Fork helper (including rejection of suffix-lookalike maps), the rendered
Cartesian shoreline lookup, and the real route range. Checkpoint restoration's
remaining 48.9 km constant is replaced with its already validated route bounds.
No map restriction or tolerance is weakened. The targeted Python suite passes
90 tests (`tmp/landward-presentation-tests-v1-20260915.xml`).

The new native boundary fixture initially failed because naming a UWorld does
not set GetMapName: Unreal uses the outer package. That failed v1 report is
retained. The fixture now uses a unique transient package with the proper map
name, verifies that name explicitly, and restores the original command line.
Final editor build PASS; all eight native tests PASS with no test warnings or
errors (`tmp/landward-presentation-native-v2-20260915/index.json`), including
the actual minimum/maximum route endpoints, 8,330 m, and rejected out-of-range
starts. The four presentation regressions are resolved; 13 physical failures
remain separately open. All 464 protected source/map/save/actor hashes match.

The SAME original-geometry 600-second cook remains live session45187/PID32276.
Its 400/450-second snapshots and all artificial banks pass independently, but
are not declared settled. At 450 seconds the instantaneous total boundary flux
is still approximately +1.255 cubic metres/second. Never mix that water with
the different landward bed or restart on observation timeout.

Last uncontended ordinary gameplay remains 24.225877 FPS / p95 47.78 ms:
FAIL against 30 FPS / 33.333333 ms. Source-supported flanks, convincing breaking
and froth, actual raft contact/traversal, hydraulic settling, remaining runtime
costs, 13 physical regressions, Colorado then Pacuare then Futaleufu, other-scene
water including Chilko/Zambezi, crew, normalization and release remain OPEN.
