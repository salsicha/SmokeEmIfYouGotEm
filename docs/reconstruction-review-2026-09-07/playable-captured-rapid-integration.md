# Captured Troublemaker connected to normal gameplay

September 12, 2026 UTC. The preceding goal pass was progress: transported foam
was installed in normal FullReach gameplay. This pass integrates the bounded
captured rapid itself. The full South Fork reconstruction and ordered goal
remain incomplete.

## What now launches

The existing **Troublemaker Rapid Challenge** menu entry now opens
`/Game/RaftSim/Maps/L_SouthFork_Troublemaker`, not the legacy FullReach station 8320
substitute. No geometry/material review flags are required. The native gameplay
mode supplies the guide, crew, run HUD, scoring and normal controls. The briefing
explicitly calls the underwater bed inferred and the reconstruction unfinished.

This is a bounded 270 m reconstructed section, not the 33.334 km corrected full
route. The other five South Fork section/full-descent entries still use the
old approximately 49 km FullReach. The FullReach ripple/foam improvements remain
there; they were not discarded or presented as full terrain migration.

`integrate_south_fork_playable_rapid.py` creates a new gameplay map from the
corrected geographic registered-rock map. It retains the exact source mesh,
reflected terrain transform, saved raft/start transform, fixed 270×162 m water
extent, 1.5 m presentation lattice, and source-matched hydraulic configuration.
The ordinary runtime now selects the existing shared carrier/raft-support
breaking relief for this exact map/data identity. The separate stateful/GPU
particle experiments remain excluded; the rejected liquid solver was not enabled.

The native game mode replaces the diagnostic blueprint game mode; the copied
validation director was omitted so normal gameplay owns its optional director.
The original review map and its actors are untouched and remain available.
Existing rights-tracked world-projected rock PBR replaces the checkerboard as a
component material override. It adds no displacement or fixed artificial wet
line. Texture appearance is artistic, not another surveyed measurement.

## Data identity and package wiring

`stage_south_fork_playable_fields.py` verified and copied the manifest, five
NumPy arrays and corrected geographic coordinate map to:

`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow`

Every copied byte retains its source hash. A separate delivery record states
the bounded/incomplete scope. The original validation-false metadata remains
false: integration is not physical/photoreal acceptance. Original tmp paths in
provenance are historical references, not runtime load dependencies.

- Geometry identity: `4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
- Original geographic map unchanged:
  `36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
- New gameplay map: `27a8d394bbafb18ff2206e1600886c98c23e9677f52bccbfa39bc6d9e6cc1299`.
- New map is in MapsToCook. The build receipt includes all 8 playable-flow
  runtime files. This is staging configuration evidence, not a completed cook.
- A fresh-process asset-registry audit resolves 11 game-asset dependencies and
  confirms no dependencies on the never-cook review-map/SurveyCandidate folders.
  The initial same-process inventory listed only 4 immediate/new packages;
  the fresh-process closure is the authoritative dependency evidence.

## Normal gameplay and verification

The captured frame has negative-to-positive local stations. Run start,
completion and progress now use a valid station interval rather than assuming
stations must be nonnegative. Challenge bounds are −60..110 m; the saved lateral −9 m
entry is retained rather than spawning at a legacy centreline marker.

An opt-in `RaftSimEphemeralProfile` creates an in-memory test profile without
loading or writing the user's slot. Its optional `RaftSimScenario` selects the
normal catalog scenario for automated runs only. Ordinary player saves behave
as before. The real slot hash remained
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`
before/after both complete traversal runs.

- Build12946 succeeded in80.92s. Existing Chaos runner float-conversion warnings
  remain. Material initialization fix build97860 succeeded in32.89s; strengthened
  traversal test build77779 succeeded in17.06s.
- Map integration32392 passed254 actual terrain collision-height probes;
  maximum error0.003866cm, unchanged captured source.
- Fresh package audit43610 passed.
- First guided traversal28454 reached the outlet and passed its old numerical
  checks, but images showed nearly invisible calm water. Renaming the copied
  material had bypassed a name-based runtime initialization guard. This first
  pass is NOT accepted as a visual delivery. The runtime now recognizes the
  explicit playable map/data configuration independently of the old material
  name. No wetness, route or collision gate was weakened.
- The strengthened rerun76911 passes with the existing
  `r.MotionVectorSimulation` render-thread warning (not suppressed).
  It also requires actual calm/active material coverage and correct native
  run-manager progress throughout the negative-station traversal.

Rerun results (`SouthForkGuidedTraversal_20260912_012542.json`):

| Measurement | Result |
| --- | ---: |
| Duration |64.506 s|
| Start→end station |−55.515→110.194 m|
| Maximum guided-route error |4.043 m (existing 5 m limit)|
| Wet samples |570|
| Missing terrain queries / grounded samples |0 /0|
| Minimum sampled tube clearance |32.113 cm|
| Fixed-location water checks |2,280; 0 missing|
| Maximum submitted hull-mask alpha error |0.001935 (<1/255)|
| Shared carrier/support ownership |held throughout|
| Material coverage / gameplay progress |held throughout|
| Maximum resolved breaking sites |6|

Zero grounded samples do not prove impact/wrap behavior. Sampled coverage and
collision do not establish every shoreline contact or calibrated real hydraulics.

13 station captures exist for each traversal. Corrected frame001 was inspected,
as were the first/last frames of a separate twelve-frame normal `-game` capture
at1280×720. The latter spans world10.315754–13.060773s with unpowered raft speed
2.18→2.26m/s. Water and captured rock-constrained geometry are visible. Earlier
failed-initialization frames003/006 remain retained as failure evidence.
The corrected scene is still coarse: blocky connected rock faces, angular
water/rock boundaries, sparse scenery and insufficient realistic breaking froth.
It does not pass the documented real-footage comparison.

26 focused Python functions pass, covering new launch/data/package/negative
station/profile guards and existing South Fork, Chilko and Futaleufu optical
regressions. They were invoked with runpy; this is not a whole-project test pass.

## Short normal-game performance

Separate normal-game run: 10 s warmup, 12 s sampling, 1280×720, 87% screen percentage,
no screenshot writes, 729 sampled frames. Mean frame 16.572 ms; p95 23.838 ms;
mean GPU 6.822 ms; mean wall-clock frame 16.484 ms. The report remains **failed**:
frame and solver budget gates do not pass. This small, sparsely dressed map is
not comparable to the legacy full-scene workload and is not packaged release
qualification. Existing engine Python startup errors also remain.

## Evidence paths and next work

Repository-relative primary artifacts:

- `unreal/Saved/RaftSimValidation/southfork-playable-integration-20260912.json`
- `unreal/Saved/RaftSimValidation/southfork-playable-package-20260912.json`
- `unreal/Saved/RaftSimValidation/southfork-playable-traversal-v2-20260912/index.json`
- `unreal/Saved/Automation/SouthForkGuidedTraversal_20260912_012542.json`
- `unreal/Saved/Screenshots/southfork_captured_playable_20260912_000.png` through011.
- `unreal/Saved/RaftSimValidation/southfork_captured_playable_perf_20260912.json`
- Corresponding named logs under `unreal/Saved/Logs`.

All listed builds, editor audits, traversals, game captures and performance runs
are terminal. No final project commit or completion claim. Next refine the
coarse connected rock/shore geometry and physical breaking water against the
captured sources on this now-playable path, then continue coordinated full-route
migration and the unchanged remaining queue. Do not retreat into isolated-only
fixtures or confuse the bounded challenge with completed South Fork.
