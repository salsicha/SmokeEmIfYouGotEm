# Captured canopy connected to the South Fork scenario

September 12, 2026, 19:45 UTC. South Fork is the playable scenario;
Troublemaker is only an in-river rapid and is absent from the scenario catalog.
The existing canopy was stranded in the retired isolated rapid map. This was
a real missing-progress integration gap, independent of water fidelity.

`prepare_south_fork_canopy_placement.py` retains all 1,268 original inferred
placements and source hashes. Exact current rapid triangles still match their
roots within 7.11e-13 cm; all 102,708 dry-collar checks pass. Two Python tests
verify translation without a second north reflection and reject invalid inputs.
The placement manifest is
`full_reach/playable_route/captured_canopy_placement_v1.json`, SHA256
`7147f349c5d32893440b2bf63ebd404aedebadceab1751ee4ae2a9f78cbc347c`.

The guarded editor integration adds exactly one native canopy actor to
`/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`. Its three static, non-colliding
HISM components contain 425/420/423 instances. Their local coordinates already
use east/-north; only the rapid-to-full-river translation is applied. Height is
scaled from the existing mesh bounds, including the actual mesh base pivot.
No random scatter, runtime tick, terrain deformation or hydraulic edits.

## Saved result

- Saved map reload passes all 1,268 transforms/heights and all 1,268 root
  collision probes, maximum collision error 0.000771483 cm against 0.1 cm gate.
- All 455 pre-existing external actor packages, source assets and player save
  remain byte-identical. There are now 456 external actors, exactly one canopy.
- Eleven canopy mesh/material/texture dependencies are in shipping folders;
  no never-cook review-folder dependencies are introduced by this canopy.
- Map SHA256 is `db3080cc87f82bafbcb5403757fead35ca6b7a5d4b52dc74c35548d5faf7abb6`.
- New actor package is
  `/Game/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach/2/NQ/TG2GGREZPJAESZ7ZRZYHNQ`,
  SHA256 `6ae0f5055ae15c3b3b4279efffbb7952aa830ce9443e5b395a8e6e7afff8f427`.
- Pre-change map and all previous external-package hashes are retained in
  `unreal/Saved/RaftSimValidation/south-fork-before-canopy-integration-v1-20260912.zip`,
  SHA256 `54bee1157f4137696633f96607de4541eeea8d363d8359e058358e0d72165d69`.
  Undo must identify only this new actor package and restore the backed-up map;
  do not recursively delete the external-actor directory.

Detailed evidence is
`unreal/Saved/RaftSimValidation/south-fork-canopy-integration-v1-20260912.json`.
The editor script reports all assertions passed and no Python traceback; its
host process returned 1, so that exit status is not presented as a passing test.
Fresh-process verification and actual-game visual evidence are separate checks.

The fresh read-only audit also passes all 1,268 transforms and root probes, with
identical errors and no duplicate actor. Its evidence is
`unreal/Saved/RaftSimValidation/south-fork-canopy-fresh-audit-v1-20260912.json`.
It reports passed assertions without a Python traceback; host exit is again 1.
The separate native regression process exits 0: all 34 tests pass, no warnings
or failures, including CareerCatalog and ProgressionMigration. Report:
`unreal/Saved/RaftSimValidation/south-fork-canopy-regressions-v1-20260912/index.json`.

## Actual normal-game capture

Fresh `-game` launch of the South Fork scenario at review checkpoint 8330,
ephemeral profile, fixed camera `-543700 -359000 1800 -25 -130`, no water or
physics overrides. Process exits 0. Twenty unique screenshots span 5.659 s
of game time; camera displacement is zero. Requested intervals are not exact
GPU exposure times. Neither screenshot nor recording cadence is FPS evidence.

- Frames: `unreal/Saved/Screenshots/south-fork-normal-canopy-v1-20260912_000.png`
  through `_019.png`; frames 000 and 019 inspected against the earlier bare-bank
  frame `south-fork-normal-froth-motion-v1-20260912_000.png` at the same camera.
- Movie: `unreal/Saved/VideoCaptures/RaftSim_20260912-124638.mp4`, SHA256
  `ae0c79b04d83f37ea1aee2eb0d5ac102c2aff352f47279827f155184320e11fc`.
  Recorder reports 73 source frames over 10.338 s; encoded frames may repeat.
- Frame audit: `tmp/south-fork-normal-canopy-motion-audit-v1-20260912.json`.

Trees and their shadows are visibly present on the rapid banks in normal
gameplay. The existing coarse/repetitive leaf clusters and uniform whitewater
patches remain visible too. These images verify integration, not photorealism,
complete river coverage, correct local froth trajectories or crest acceptance.

## Not acceptance

This covers only the original 360 x 280 m rapid survey footprint, not all 33 km
of banks. Inventory, individual trunk positions, species, crowns and mesh forms
remain inferred; the existing tree forms were previously rejected as photoreal.
No tree collision is supplied. Full bank ecology, convincing froth/breaking
motion, guided-line recovery, performance and all later river/crew/release work
remain open. The underlying river and hydraulic geometry are unchanged here.
