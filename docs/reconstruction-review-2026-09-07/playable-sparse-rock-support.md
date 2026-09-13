# Playable captured-rock support correction — 2026-09-12

The normal **Troublemaker Rapid Challenge** now includes 420 additional captured
returns, their revised connecting triangles and a matching recooked flow field.
This is an incremental geometry correction, not completed terrain/rapid realism.
The existing normal-game crest refinement and transported froth remain enabled.

## Cause and bounded correction

The previous two-return-per-cell gate discarded sparse returns in the already
photo-reviewed rock regions. Its empty cells retained the inferred deep bed,
creating steep connecting faces between neighbouring rock samples. A source
audit found 556 connected candidate cells with the original >0.3m-above-water
threshold; lowering that threshold added few cells and was not accepted.

The correction retains a candidate only when at least two ORIGINAL rock
neighbours within the adjacent 0.5m-grid neighbourhood corroborate its height
(within 1m of their range). No recursive propagation, water-level returns,
outside-region expansion, random geometry or smoothing of measured anchors.
420 cells pass; 388 had only one eligible return. These class-1 returns remain
interpreted rock candidates, not certified ground classifications. Their exact
source XY and lower-envelope height are retained. All previous ground/rock
measurements and all other vertices are unchanged.

Steep rock-to-inferred-bed face area falls from 2,602.918m² to 2,383.077m² (8.45%).
Most steep sides therefore remain unresolved. This does not justify calling the
whole bank or rapid shape corrected. Underwater bathymetry remains inferred.

## Shared geometry, flow and collision

- Source mesh: `tmp/troublemaker-sparse-rock-support-20260912/registered_mesh_source.npz`,
  SHA `41f92d72102dbc4140638eb9cf97aed3b58e1ffc55bf8b6abbbcd38df7bd4089`.
- 403,200 vertices / 803,842 triangles; no render/collision decimation.
- Every triangle sampled at centroid, asymmetric barycentric point and shared
  edge: maximum error 2.04814e-12m. Existing measured anchors remain unchanged.
- 274 cells of the actual 1m hydraulic bed change. Triangle re-partitioning can
  lower an interpolated cell as well as raise it: delta range −0.45435..3.28618m.
- Identical forcing, 6000 × 0.1s, HLL/MUSCL, CFL .2, 45.3069545472m³/s inlet.
  Solve terminal/passed in 238.833s; all 13 saved frames pass sanity checks.
- Tail section flux error 1.626%; storage and <1cm regional-stage settling gates
  pass. Independent numerical face-flux audit passes: inflow45.30695,
  outflow45.20816m³/s, side leakage0; volume-derivative discrepancy8.19e-7m³/s.
- Ordinary map ground now references
  `/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround`.
  2,644 collision traces pass, maximum error .0292702cm (unchanged .1cm gate).
- Map SHA `5e5bfe7f7b90919d04d8c8db0b2b0f15c4b99a5b5f5253b1e5fc7c7e8164a50f`;
  mesh asset SHA `1ffe2b72bf1805d0d9bc722e94ab645e0c84ab162721b6560e7e789890e51a21`.
- The source-class texture is regenerated for the new support; material graphs,
  original review mesh/map, normal gameplay settings and coordinate frame remain
  unchanged. New texture asset SHA
  `5b02de5c332406eaabb225961d9890fcb49d2fe4bd04504572992444d8173bde`.

Original playable flow, map, texture and guided route are retained in
`tmp/troublemaker-playable-before-sparse-rock-20260912`. The normal route's guidance
points are unchanged; only its source/flow identity is revised. No traversal
gate or steering force was relaxed. Existing historical audits verify the
explicit old-backup/new-asset identity chain instead of silently skipping it.

## Verification status

Native traversal module build passed (19.43s). Thirty focused Python tests pass,
including six sparse-support guards and the existing playable water/launch/
canopy guards. Integration script wrote its success report and exited cleanly
without logged Python/fatal errors; the command wrapper returned exit1, so the
fresh-load audit and actual traversal remain necessary independent checks.

Final focused regression set: **52 Python tests pass**, including seven sparse
support tests, existing playable crest/froth/launch/canopy guards and other-river
water-presentation regressions. Scoped diff whitespace check passes.

Actual native traversal passes with the pre-existing MotionVectorSimulation
warning: 62.625s, outlet110.132m, maximum route error3.141m, 562 wet samples,
zero missing ground/surface queries and zero grounded samples. Minimum tube
clearance30.891cm; all2,248 fixed water checks pass; submitted alpha error
.00159469<1/255. It verifies the NEW mesh path, matching flow/route identities,
one shared carrier and normal gameplay progress. This one pass is not a fix
for the earlier timing-sensitive route failure or broad controller robustness.

Report: `unreal/Saved/RaftSimValidation/troublemaker-sparse-rock-traversal-20260912/index.json`;
samples: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260912_032732.json`.
Thirteen station captures were generated; crux004 was inspected. Separate normal
`-game` capture series `troublemaker_sparse_rock_playable_20260912_000..003.png`
is terminal; frame003 was inspected. Large flat-sided rocks are STILL obvious
at the approach; froth is visible at the crux, but breaking motion and overall
realism are not accepted. The 8.45% geometric correction is not a large visible
transformation of the scene, and should not be presented as one.

Independent fresh-load audit38372 exits0 and passes saved map/new mesh/flow
identity, unchanged ground normal/roughness/WPO and water-froth graphs. Package
closure remains24 game assets without never-cook review dependencies. This is
not a packaged release. The original user save SHA remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.

Final separate performance check:661 frames, mean18.294ms, p9529.798ms,
meanGPU7.426ms, mean solver8.666ms. Frame16.667ms and solver1.6ms gates FAIL;
memory passes. This is effectively the prior cost level, not a demonstrated
performance improvement. Report: `troublemaker_sparse_rock_perf_20260912.json`.
Graphics/content were not hidden or reduced. All owned engine, solver, export,
build and audit jobs are terminal; process inventory is empty at03:32UTC.

Breaking realism, most inferred rock sides, performance, full South Fork route
and later rivers remain open. No final commit or goal completion. Next work
must address the unresolved connecting-face/shore shape and actual breaking
motion/runtime cost, not rerun this recovery or imply that measured tops also
survey the unobserved side faces.
