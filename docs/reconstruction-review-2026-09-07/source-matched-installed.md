# Source-matched terrain, rock and water installed in normal South Fork

September 17, 2026. This is an incremental **normal-play delivery**, not closure
of the South Fork acceptance gates or the remaining project queue.

## What changed

The existing `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach` now uses the
source-consistent 4950-second full-river hydraulic state, its revised ground,
and captured-rock solid with inferred flanks. No preview flag is required.
All five South Fork catalog contracts and the full 33.334 km route remain;
Troublemaker is a rapid inside South Fork, never a menu scenario.

The original rapid terrain actor was reused, not covered with a second ground
actor. Its replacement has 803,842 directed triangles; the rock solid has 6,404.
Both production duplicates retain the exact verified CPU collision source,
original geographic transform/material, complex collision and complete render
fallback. The fallback policy is saved on the components, so it survives World
Partition reload without the old asset-name hook or temporary residency source.
The scene still has one water carrier. No material, route, launch transform,
player save, nonlinear GPU solver enablement or quality tolerance was changed.

Saved production assets are in
`/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SourceMatched20260917`.
New runtime data is the content-addressed `south_fork_source_matched_v2` bundle:
2,405 exact payloads / 917,948,199 logical bytes. Build rules now select this
bundle and validate saved scene identities, not the historical 600-second bundle.
The old bundle and old source meshes are retained.

## Provenance and safeguards

The submerged bed remains an uncalibrated shore-distance prior. Removing its
inferred shelf/plunge changes 2,132 authority-2 vertices, not captured XYZ,
registered XY/topology or the rapid seam. Rock flanks are inferred. Byte-exact
source mesh/cap and historical provenance manifests are archived in
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/source_matched_20260917`.
Historical experimental flags were not rewritten to imply acceptance.

Native pre-installation evidence verifies 25,600 field queries, zero wet-state
mismatches, 64,935 collision queries and all 803,842 directed terrain triangles.
Maximum collision position error is 0.031770 cm against the unchanged 0.1 cm gate.
Runtime export verifies 42,185,039 overlapping bed samples and all 799 source
windows. Coverage retains 406,823 original water probes with at least 10 m
interior margin (required 8 m); independent re-audit finds no failed rectangles.
These source/load checks do not prove settled flow or dynamic full-raft contact.

All five actual native catalog starts are wet and finite before and after 120
steps at 1/120 s. This independent crop preflight is not the game-mode launch
selector or a complete traversal. A first invocation failed on an unnecessary
NumPy import before testing water; the dependency was made lazy and the failed
log preserved. The successful run changed no saved files.

Installation archives and verifies exact prior map/external-actor packages
before mutation. Only the config actor, original terrain actor and map changed;
one rock actor and two production meshes were added. Fresh-process reload
verifies 457 actor descriptors, exact native mesh identities, persisted fallback
flags, new hydraulic bindings and all five unchanged catalog contracts.
131 focused Python tests pass, including native-import, launch-margin, source
identity, retention/staging and runtime-bundle rejection controls.
The adjacent 13 exact-terrain replacement tests also pass. The 131-test group
was rerun after installation with the same result.

Compact immutable receipts are archived beside this note:

- `source-matched-installed-receipt.json`: installation/source identities and
  exact recoverable backup location/hash.
- `source-matched-installed-bindings.json`: fresh native saved-scene bindings
  consumed by the runtime packager.
- `source-matched-native-4950s.json`: matching source/collision/initial-water proof.

## Actual normal gameplay and remaining limitations

The no-preview ordinary full-descent capture starts at the existing explicit
8330 m review station in the normal map; it is not a complete menu-to-finish run.
It exits zero, emits 24 original 1280x720 PNGs, and logs `singleSurface=1`.
`unreal/Saved/VideoCaptures/RaftSim_20260917-132118.mp4` fully decodes to 478
frames through 15.9 seconds, with 22 adjacent duplicates. Its SHA-256 is
`0e6573569ec13640b2460d9611c0ddbb176ad7fa460fdcaabc158eb680121957`.
Encoded frame rate is not simulation performance. The engine's unrelated
experimental Python Toolset initialization errors remain in the log.

Inspected normal PNG 022 and decoded 6/11-second frames show the revised rapid,
localized whitewater near the ledge and no equivalent abrupt foreground mean
face. They still show broad soft foam, smoothed rock detail, uniform vegetation
and detached-looking spray. Trajectories/cameras differ from older recordings;
no exact pixel causality or final visual acceptance is claimed.

Both reference videos were accessible in the preceding capture pass:
Qweniden's `2XTbOCNDcZQ` at about 0:40 and 1:08/1:09, and John Elkins's
`ZEG1kvjNI30` at 0:40 and 0:48. The bank view shows angular rock-divided drops,
irregular froth and dark gaps. The raft view is substantially passenger-occluded.
These are qualitative observations, not calibrated discharge/height measurements;
no reference media was downloaded or added to the repository.

The editor Development rebuild succeeded (34 actions, 710.62 seconds). The
rebuilt ordinary no-preview recording is
`unreal/Saved/VideoCaptures/RaftSim_20260917-133706.mp4`, SHA-256
`81fd9f298dcc7c5a4690a16bee5eb2fac796054adeb21cd03572d1260c648e3f`.
It fully decodes to 472 frames through 15.7 seconds with 25 adjacent duplicates;
the inspected 11-second frame retains the same broad-foam/rock-detail limitations.

Actual post-rebuild normal gameplay (300 CSV frames, inclusive rows 60..240,
1280x720 D3D12, no motion recording or preview flag) averages **35.535635 FPS**,
mean 28.140766 ms, p95 **37.5995 ms**. Game-thread mean is 27.924174 ms and GPU
mean 9.852050 ms. The exact cook was suspended/resumed successfully around the
run, which exited zero without timeout. This is still **FAIL 30 FPS / p95
33.333333 ms**, not sustained or packaged acceptance. The CSV SHA-256 is
`a692a928d6618bc5c3d4306e0ed912f3411db37acde1082a36bd19b31e3a413c`.
Do not attribute the difference from older runs solely to geometry: the runtime
was rebuilt, trajectories differ, and this is not an isolated both-order trial.

The standalone build staged all 2,405 payloads. Independent byte/closure audit
passes for the actual `unreal/Binaries/Win64/RaftSimRuntimeData` tree with no
external source fallback. Bundle manifest SHA-256:
`84d80b5455e8fa1c0b70ee20d1d0c8617507ebbd4b07420d1ad99141807c1a1c`.
Staging is not the final cooked-package or executable acceptance gate.
The standalone Development build also succeeded (2,417 actions including the
2,405 payload copies, 390.98 seconds). Its executable SHA-256 is
`4af89146dd45b833df35345735399f53ef4d7d177789e5600380137525002dd0`.
The final cooked map/package has not been regenerated or accepted in this pass;
an older packaged installation does not acquire these saved-map edits by itself.

Fresh native staged-path comparison passes 2,001 full-route queries and 2,601
initial-water queries (592 wet), with exactly zero route/field difference from
the source tree. No solver steps or asset saves occur in this comparison.
Report SHA-256:
`79b72565af6c3915977ffec62df3f76c0096c34b71f586ac61400f2ad91399b6`.
Six rebuilt native tests pass with no failures, warnings or skipped tests:
SharedCartesianAtlas, ShorelineCapturedGroundRendering, ShorelineTerrainProbe,
SurfaceSourcePacking, ShorelineExactCache and ShorelineMovingBankCache.
The unrelated compiler warnings and previously recorded physical-suite failures
are not silently closed by this selected test group.

An additional ordinary full-descent startup omits both the review-station and
preview flags. It exits zero, produces eight 1280x720 captures and logs one
water surface. Inspected put-in PNG 007 shows the crew afloat; it also exposes
the still-bare coarse tan banks at this part of the river. This is a short
normal-start check, not full river/crew/environment acceptance. Its SHA-256 is
`4c84b0b8582b97ddd7d033e5637d55ec8662a38a7de46a61d36da5c7c274e4a9`.

Before installation, the fixed reference/candidate/candidate/reference comparison
gave 25.601723 / 27.324937 / 27.736928 / 25.446253 FPS, with p95
44.7845 / 44.2542 / 43.7694 / 45.6409 ms. Candidate cost improved in both orders,
but **every run fails 30 FPS / p95 33.333333 ms**. Changed source states and
trajectories prevent treating that as a same-workload optimization benchmark.

The continuing cook's 5000, 5050 and 5100-second state AND 86,720 artificial-bank
audits pass. It remains unsteady: 5050 outflow is 119.858390 m3/s against
45.306955 m3/s inflow. Only the verified 4950 state is installed; later checkpoints
are not silently substituted. Physical breaking/froth, sustained performance,
whole-river contact/traversal, remaining regressions, packaged execution and
release stay OPEN, followed by Colorado, Pacuare, Futaleufu, Chilko/Zambezi,
crew and normalization work in the existing queue.
