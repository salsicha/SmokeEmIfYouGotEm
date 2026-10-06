# Captured-bank canopy: historical rapid-map delivery

**Superseded September 12:** South Fork is the scenario. Troublemaker is only a
rapid within it, never a selectable menu scenario. The delivery below describes
the retired isolated map, not the current playable entry. The retained 1,268
placements have now been migrated into the rebuilt South Fork full-river map;
see [current full-river integration](normal-river-canopy-integration.md).
Keep the historical source and validation records below, but do not rerun the
old isolated-map integration as a way to update normal gameplay.

September 12, 2026 UTC. This is incremental playable delivery, not South Fork
completion or photoreal acceptance. Normal entry: **Troublemaker Rapid Challenge**,
`/Game/RaftSim/Maps/L_SouthFork_Troublemaker`. No review flags required. The other
five South Fork entries still use legacy FullReach; full-route migration remains
unfinished. All later rivers, crew, release checks and final commit remain open.

## What changed

The previously bare captured banks now carry 1,268 canopy instances in three
saved hierarchical instancing components. The actor has no runtime scatter or
tick. Existing three-form project-authored live-oak woody meshes provide near,
middle and far LODs. Their July visual review was rejected as photoreal; using
them as an explicitly provisional representation here does not reverse that
finding. Current captures still show coarse leaf clusters and repeated forms.

`build_troublemaker_captured_canopy.py` reads the actual retained LiDAR and
georegistered NAIP, checking the point/mesh identities. It selects non-water
class1 returns 3.5–30 m above the source ground and co-located visibly green
image pixels, groups 3 m patches with at least 12 supporting returns, takes
90th-percentile height, and separates crown peaks deterministically. Every
inferred trunk has a 2 m dry-ground collar and sampled ground slope below 56.7°.
Roots use exact registered triangle heights and X=east/Y=south/Z=up coordinates.
No fabricated random landscape positions or missing-data fallback are used.

This is **not a surveyed tree inventory**. Class1 is unclassified, not a certified
vegetation class. RGB greenness and above-ground height constrain an interpretation;
they do not prove species, trunk location, crown shape, individual tree count or
contemporaneous conditions. Source dates differ. All those uncertainties remain
in `troublemaker/playable_canopy.json`; short vegetation is not reconstructed.
Canopy has no collision and is outside the inferred wet bed. Physical tree
obstacles, complete bank ecology and photoreal tree morphology remain unverified.

The original captured ground mesh, its complex collision, and every staged
hydraulic array remain byte-identical. No rock vertices or inferred riverbed were
altered to make tree roots fit. The gameplay map changed from
`27a8d394bbafb18ff2206e1600886c98c23e9677f52bccbfa39bc6d9e6cc1299` to
`743a420632a767a78b56779705e394091c94a6f0ad2cdb04a5be3f60ca25f862`.
A byte-identical pre-canopy map backup is retained under
`tmp/troublemaker-canopy-map-backup/27a8d394bbafb18ff2206e1600886c98c23e9677f52bccbfa39bc6d9e6cc1299.umap`.

## Rock-face diagnosis

`captured-rock-selection-edge-audit.json` identifies 3,121 rock-to-inferred-bed
connecting faces steeper than 60°, totaling 2,602.918 m². Only 564 faces/469.255 m²
are within 0.75 m of interpreted search-region edges. Most steep connecting
faces are therefore not directly on those edges; this does not prove a complete
cause or a correct rock outline. All 4,226 selected original rock returns are
class1, selected through existing photo-reviewed regions. An outside-region
check using only classified ground found 23 eligible points and **zero** supported
additional cells. Blindly expanding the footprint or smoothing measured points
is not justified. Submerged rock sides and connecting faces remain inferred and
visibly coarse; they still need source-consistent reconstruction with matching
collision and hydraulic recooking before geometry promotion.

## Verification so far

- Editor build 20058 passed in 26.46 s; new native canopy actor is compiled.
- Initial integration 28515 exited with a Python setter error without saving.
  The setter was replaced by checking the constructor's disabled-overlap state.
- Integration 21268/90257 rejected root probes before saving. Read-only diagnosis
  35035 showed that waiting for asynchronous asset compilation restored the same
  downward contacts at the original coordinates. Added that prerequisite before
  validation; no coordinate snapping or tolerance relaxation.
- Corrected integration 24334 passed all 1,268 root checks, max error 0.0007715 cm,
  and all 254 pre-existing ground/rock probes, max error 0.0038656 cm.
- Fresh-process audit 2293 verifies all 1,268 saved transforms and heights, max
  error 2.274e-13 cm, three components, collision disabled, and 22 game-asset
  dependencies with no dependencies in either never-cook review folder.
- Separate normal `-game` capture produced 12 frames. First/last were visually
  inspected: trees and shadows appear on banks; raft movement and water remain
  visible. Frame 11: world 13.059555 s, raft 2.26 m/s under Rest command. This is not
  a still editor viewport or an isolated review map.
- Traversal 32296 passed with the existing `r.MotionVectorSimulation` warning:
  64.464 s, station −55.476→110.062 m, maximum route error 4.520 m (unchanged 5 m
  limit), 567 wet samples, zero missing/grounded samples, minimum tube clearance
  30.602 cm. All 2,268 fixed water queries succeeded; shared carrier/support,
  actual material coverage and native run progress held throughout. Maximum
  hull-alpha submission error 0.00194423 remains below 1/255. Thirteen station captures
  exist; crux frame 004 was inspected and still does not meet real-footage water
  or foliage realism. Numerical success is not physical/visual acceptance.
- 34 focused Python functions pass across canopy, launch, Chilko/Futaleufu
  presentation and South Fork foam optics. The canopy tests include rejection
  of outside-image coordinates, no diagonal rock-gap bridge and collision
  readiness before source/root validation. This is not a full-project pass.
- Separate normal-game performance run completed: 10 s warmup, 12 s sampling,
  1280×720 at 87% screen percentage, 702 frames, no capture writes and no hidden
  canopy. Mean frame 17.138 ms, p95 24.113 ms, mean GPU 7.425 ms, mean solver
  8.770 ms. **Frame and solver budget gates still fail**. This is an offscreen
  engineering diagnostic, not packaged release qualification. No timing gate
  was changed. Report: `troublemaker_canopy_perf_20260912.json`.
- The real user save remains SHA256
  `181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
  All editor, capture, traversal and performance jobs are terminal. The full
  goal remains active; no final project commit or completion claim.

Primary evidence lives under `unreal/Saved/RaftSimValidation/`:
`troublemaker-canopy-integration-20260912.json`,
`troublemaker-canopy-fresh-audit-20260912.json`, and
`troublemaker-canopy-ground-diagnosis-20260912.json`.
Capture files: `unreal/Saved/Screenshots/troublemaker_canopy_playable_20260912_000.png`
through 011. Named logs preserve both failed attempts and corrected runs.

## Remaining work

Continue improving the actual playable rapid: source-consistent rock sides and
shorelines, physical breaking/frothy water, vegetation morphology and bank
surfaces, then coordinated full-route migration. Do not mistake visible canopy
or sampled collision agreement for real-footage, hydraulic, impact/wrap, 60 FPS
or release acceptance. The full goal remains active.
