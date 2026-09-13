# Playable crest geometry, froth and bank surfaces

September 12, 2026 UTC. The user explicitly asked to make terrain, rapid shape,
breaking waves and convincing froth work in the playable scenarios. This is an
incremental normal-game delivery, **not completion of that request**. Normal
entry: **Troublemaker Rapid Challenge**, `/Game/RaftSim/Maps/L_SouthFork_Troublemaker`.
The other five South Fork menu entries still use legacy FullReach; none was
redirected to a geographically incompatible bounded map. Later rivers remain open.

## Delivered in the ordinary runtime

- Conforming local crest refinement on the same water section: 19,729 original
  vertices retained, finally 38,488 submitted vertices and 76,398 triangles.
  Two refinement levels cover (-18,-18)..(30,18), with .1875 m third-level
  spacing confined to the steep-crest bounds (4,-8)..(17,12). The initial
  full-third-level version had 70,905 vertices and 141,232 triangles.
  Hydraulic sampling stays on the original 1.5 m presentation grid with 3 m
  analysis stride. Additional vertices replace interpolated crest relief with
  the exact continuous profile used by raft support. No new amplitude, second
  water sheet, experimental liquid solver or additional hydraulic query.
- Normals derive from the refined geometry and preserve reflected winding.
  Tangents are projected into the new normal plane. The source terrain,
  collision, hydraulic arrays and physical crest/support equations remain unchanged.
  An exact-input correction cache reuses only identical site/coarse-crest/shore
  records; no tolerance or hash approximation is used. Native cached and
  uncached vertex positions/normals compare exactly. Runtime speedup from cache
  reuse is not established; the spatial reduction is independently verified.
- Fixed a real foam-generation bug: a spilling jump whose rise is already
  resolved has zero *additional* crest height, but must still produce crest
  foam. Its height stays zero; only the erroneous early foam rejection is removed.
- The normal captured water material retains the prior transported-foam
  color/roughness/specular response and zero emission. Added bounded optical
  bubble relief from that same foam and current-advected lace, retaining the
  exact ripple subgraph. The 1.2 cm optical bump parameter and .65 slope cap
  are appearance choices, not measured bubbles or physical geometry.
- The normal ground instance now uses a dedicated captured-ground parent,
  registered NAIP bank color and a numeric source-authority texture. Inferred
  bed receives no aerial drape; dry cells next to the water boundary have a
  one-cell exclusion ring. Steep faces retain world-projected rock PBR.
  Rock-support cells receive a neutral mineral tint. Full-strength drape looked
  flat/bright in-game, so retained PBR detail and reduced drape weight to .55.
  Aerial imagery contains capture lighting, shadows, canopy and roofs; it is
  **not calibrated intrinsic ground albedo** or newly reconstructed geometry.

No rock vertices were smoothed or replaced and no inferred connecting face was
relabelled as surveyed rock. The block-like rock sides and absent small-scale
rock/shore morphology are still visible and remain a major unfinished item.

## Evidence and failures retained

Baseline normal-game audit at world time 10.002 s found six persistent sites.
The analytic crest reached .48643 m. The old 1.5 m triangles missed up to
.122957 m of that profile on quarter-cell samples. A previously logged .022 m
crest was a startup-envelope value, not the settled height. The earlier
`troublemaker_settled_height_20260912.log` is terminal: 51 candidate comparisons,
42 accepted before spatial deduplication, max inferred extra height .5638 m at
station 12/lateral 6. Those are not 42 distinct published crests.

The first two-level refinement native fixture reduced centroid error from
.172028 to .020472 m but **failed** its new unchanged .02 m gate. Tightened local
refinement, not the threshold. Final fixture error is .006384 m in both world
orientations; source vertex error below .000004 cm. Four native tests pass:
`PlayableCrestReconstruction`, `HydraulicCrestScale`, `SpatialBreakingLocality`,
`ConformingSurfaceRefinement`. Forty-five focused Python functions also pass.

Actual normal-game CPU mesh audit: 100,572 nonzero-shore triangle-centroid
samples, maximum crest-component error .01615251 m and **zero source-vertex
position change**. This is not directly the same sample set as the old
quarter-cell audit and does not measure all base/pocket relief or bathymetry.
Artifact: `unreal/Saved/RaftSimValidation/troublemaker_playable_crest_sampling_fine_20260912.json.mesh.json`.
The final optimized normal-game audit checks 44,707 triangle centroids:
maximum .01614431 m, still zero source-vertex position change. Its artifact is
`troublemaker_playable_crest_sampling_optimized_20260912.json.mesh.json` in the
same directory. Four native tests pass again in `playable-crest-tests-optimized-20260912`,
including exact cached/uncached parity; the fixture error remains .006384 m.
Build 28617 passed in 143.02 s. Final fresh material/source audit 58547 passes.

Build 21544 passed (138.65 s). Build 68991 failed on diagnostic JSON API use;
fixed in 6530 (33.67 s). Final tangent-basis build 42323 passed (33.68 s).
The failed native run `playable-crest-tests-20260912` is retained; the passing
run is `playable-crest-tests-fine-20260912`.

Two-level traversal 77969 passed existing gates with the existing
MotionVectorSimulation warning. Three-level combined traversal 53382 reached
110.159 m in 67.870 s with zero missing ground queries/grounded samples and
minimum tube clearance 32.252 cm, but **failed** the unchanged 5 m route limit:
maximum 5.15804 m at station 52.4, lateral 6.142. All 2,336 fixed water checks
passed. No physical force or guide-control gain was changed to hide that failure.
Frame pacing/control sensitivity is a hypothesis, not an established cause.
Do not discard this failed run if a later run passes.
Final optimized traversal 85025 **passes** the unchanged gates with the existing
MotionVectorSimulation warning: 63.154 s, outlet 110.146 m, max route error
3.624 m, 559 wet samples, zero missing ground/grounded samples, minimum tube
clearance 29.865 cm. All 2,236 fixed water checks pass; maximum submitted hull
alpha error .0019134 remains below 1/255. This single successful optimized run
does not erase the earlier 5.158 m failure or establish broad timing robustness.
Report: `troublemaker-playable-surfaces-optimized-traversal-20260912/index.json`;
samples: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260912_030533.json`.
Thirteen station captures were produced; the crux frame004 was inspected.
Normal `-game` captures `troublemaker_playable_surfaces_final_20260912_000.png`
through 003 were also inspected first/last: current and froth move, rock sides
remain visibly block-like. Final bank drape is less bright than the first version.

Initial integrated performance (before spatial/cache optimization): 614 frames,
mean 19.670 ms, p95 34.578 ms, mean GPU 7.450 ms, solver 8.701 ms. Frame and
solver gates **fail**. The run is terminal and retained as
`troublemaker_playable_surfaces_perf_20260912.json`; it is not release-eligible.
Final optimized separate normal-game performance: 655 frames, mean 18.468 ms,
p95 29.978 ms, mean GPU 7.415 ms and solver 8.650 ms. This improves the initial
refinement's 34.578 ms p95, but is still slower than the preceding coarse
carrier's 24.018 ms p95. Frame and solver gates remain **failed**. Report:
`troublemaker_playable_surfaces_optimized_perf_20260912.json`. No runtime cache
reuse milestone was logged during this sample; do not attribute the improvement
to the cache without evidence. No content or graphics setting was hidden/lowered.

Fresh saved-material/flow/source audit 2205 passed; dependency closure contains
24 game assets, with no never-cook survey-review dependencies. This is not a
completed cook or release test. The ground color was subsequently reduced after
visual review; final verification and performance results are recorded below.

## Asset identity and recovery

Water material changed from `0b13bf122ea85264b219c536c61067a6c31597e5b438e6b66e844d01a2e8a864`
to `c6c119ac1139a0aa7fa9cb5b746142ff1c9ad9b80c31a7a2e3c8354d8812c7fa`.
Byte-identical original retained in `tmp/troublemaker-foam-material-backup/`.
Ground-instance original retained in `tmp/troublemaker-ground-material-backup/`
as `982cbcea6919bf95b3d0e286c595694829e242ddfeba22049947dee1b31930b1.uasset`.
Ground instance now has SHA `a7f0d43bad89b1a4555881067e0d4d6ceea1e2409aea9d11ce481b1d5efa819b`.
Detailed graph/texture/geometry identities and the first drape revision backup
are in `troublemaker-surface-color-20260912.json` and
`playable-froth-normal-setup-20260912.json` under `unreal/Saved/RaftSimValidation/`.

The map stays `743a420632a767a78b56779705e394091c94a6f0ad2cdb04a5be3f60ca25f862`;
ground/collision mesh stays `12ba8d8ac76f378cedfdb6c5cc8bd7e8708b0914a9aa43c9389e6753e0d90d56`.
All staged flow and coordinate-map hashes were freshly verified unchanged.
Final ground parent SHA: `f35b734c0b888c1e046939692ce14ca4b9aeb67689987f2b9211c50afdad1733`.
Real user save remains `181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.

## Remaining acceptance work

The wave profile is sampled more accurately; this does not make the modeled
rapid match real footage or provide physically overturning water. Froth,
terrain/rock sides, shoreline shape and trees are not visually accepted.
Performance and route robustness must be resolved, not merely rerun until a
pass. Continue normal-playable delivery, then matched full-route/scenario
migration and the remaining river queue. The full goal remains active.
All owned engine/build/validation runs from this pass are terminal. No final
commit, full-scenario acceptance or goal completion. The user can see this
increment by launching **Troublemaker Rapid Challenge** normally; no review flag
is required. Prioritize the still-obvious rock/shore geometry and rapid motion,
not another isolated-only material variation or unchanged rejected volume solve.
