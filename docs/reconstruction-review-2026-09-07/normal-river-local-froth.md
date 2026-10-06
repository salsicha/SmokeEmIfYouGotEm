# Local-current froth in playable South Fork

September12 follow-up: [local shading and shorter optical renewal](normal-river-local-shading.md)
supersede the four-second material below. Both froth and gradient normals now
follow local UV1 current on a one-second phase clock; material3733e083….
Actual before/after game samples show shorter streaks, but full visual and
performance acceptance remain open. Historical reports/hashes below retained.

September 12, 2026, 20:12 UTC. Incremental implementation and game verification,
not visual, hydraulic, performance or full-scene acceptance. South Fork remains
the scenario; Troublemaker is only a rapid inside it, never a menu entry.

## Two actual motion problems addressed

`RaftSimWaterSurfaceActor.cpp` cleared each presentation-flow value immediately
before smoothing it. Ordinary currents therefore blended from zero on every
refresh instead of converging toward the actual local current. The new
`RaftSimWaterFlowHistory::Advance` call retains the previous wet-cell velocity;
dry cells still clear, and the existing immediate response to large changes is
preserved. This changes presentation UV1 data, not the solver's momentum.
Native `RaftSim.Water.LocalFlowHistory` verifies convergence, source cross-flow
sign, timestep consistency, zero-time history and the existing large-change rule.

The South Fork optical lace previously used one current displacement sampled
at the raft throughout the visible water. Its four foam optical consumers now
receive `RaftSimLocalFoamLace.hlsl`: local source-frame UV1 velocity, UV0 plus
the moving source origin, and real material time. Two staggered four-second
backtraces keep deformation bounded and cross-fade without a reset seam. Zero
flow does not animate by itself. Source north is not reflected a second time.
This is a **local frozen-velocity optical approximation**, not persistent
Lagrangian particle history or a measured bubble model.

The first installed revision averaged lace values before thresholding. Actual
capture exposed washed-out holes; revision 2 retains both samples until after
their optical coverage calculation, then blends coverage. It preserves the
existing optical density, transported vertex-red foam amount, texture, scale,
rotation and curl. No extra speed-derived foam, extra water sheet or force.
The inherited gradient-normal branch still uses the shared raft-current integral;
that mismatch, four-second optical renewal and excessive streaking remain
review items, not claimed resolved local fluid detail.

## Authoritative implementation evidence

- Builds v1/v2 succeed in 85.76/41.01 s. Current RaftSimRaft DLL SHA256
  `5b5edff1e7f84d7d911c378ed02923ccd3c538e93ed099c006b8af52191d1e0b`;
  main game DLL remains `069df27a76fd16b43120d5b19ec1865e987825484c58a52f28868a277582cf1f`.
- All 35 native regressions pass, no warnings/failures, including the new
  flow-history test and previous 34 shoreline, crest, packing, catalog and save
  tests. Report `unreal/Saved/RaftSimValidation/south-fork-local-froth-regressions-v1-20260912/index.json`.
  The subsequent v2 change is editor-authored optical coverage, not new runtime
  C++ or a repeat of those unit-test assertions against photographs.
- Six analytical Python phase/callsite checks pass, plus two graph-signature
  checks and two later-bank-observation provenance checks. Phase checks are
  mathematical contracts, not GPU or image-quality acceptance.
- Guarded v1/v2 installation verifies unchanged WPO, opacity-mask and normal
  graphs; four optical consumers; origin exactly once; physical UV1 velocity;
  no raft-current dependency in the new optical-lace branch; refresh idempotence
  at 689 expressions. Map, external actors, ground asset and user save unchanged.
- Current material SHA256 `d55e5cdc8831cf9c084f4e9516eff0f225fa0c6b76444722d4832e2b2a254c3b`;
  shader SHA256 `8e39c65288cb99cb32229362832ca824346eba995711b0c4fb049c40483d0e44`.
- Material backups `south-fork-before-local-froth-v1-20260912.zip` and `...v2...`
  are retained under `unreal/Saved/RaftSimValidation/`. Original pre-local
  material hash `06ed556dbf027e705f0d93f2def1974c2a20092ea36f9932958657bf778b5c57`.

Installation reports are `south-fork-local-froth-integration-v{1,2}-20260912.json`
under that validation directory. Installer processes returned 1 despite passed
assertions and no Python traceback, so their exit statuses are not cited as
test passes. A fresh audit initially failed because Python wrapper addresses
were serialized in texture/default-value strings. Corrected comparison strips
only those process-local addresses; texture paths, numeric values, shader code
and all links remain significant. Two tests enforce that distinction. Fresh
audit v3 process exits 0 and produces
`south-fork-local-froth-fresh-v2-20260912.json`, proving saved v2 graph identity.
The failed v2 audit log is retained, not overwritten or misreported as passing.

## Actual current-map result

Normal `-game`, South Fork scenario, ephemeral checkpoint 8330, same fixed camera
`-543700 -359000 1800 -25 -130`, 1280x720, no physics/material override. Process
96138 exits 0. Actual screenshots 000/020/039 inspected: local lace stretches
through the current, but bright uniform areas and excessive streaks remain.
The screenshot series is not itself continuous-motion or trajectory acceptance.

- `unreal/Saved/Screenshots/south-fork-local-froth-v2-20260912_000.png` through
  `_039.png`: 40 unique images over 11.82 s of sampled game time, fixed camera.
- `unreal/Saved/VideoCaptures/RaftSim_20260912-130739.mp4`, SHA256
  `78c8ac5296b2c0face7da349c1f678f9bb00ba239bbf75fa120246c6227f034c`.
  Recorder: 93 source frames, 16.368 s; encoded frames may repeat. No FPS claim.
- `tmp/south-fork-local-froth-motion-audit-v2-20260912.json`: timing/file audit,
  not physically correct flow, exposure-time registration or visual acceptance.
- `tmp/south-fork-local-froth-crest-v2-20260912.json.cartesian-mesh.json`:
  712,224 samples, max target error 1.427267 cm under unchanged 2 cm gate;
  source vertex change 0; fine correction tracking error 0.125440 cm. This
  excludes other base relief, macro temporal lag and GPU perturbations.

Bank-side reference replay was attempted through browser and node runtimes;
both failed initialization with `failed to write kernel assets` / missing path.
No new remote footage was watched, downloaded or registered. Existing dated
reference interpretations remain historical evidence, not a fresh comparison.

NEXT: physical crest/trough and froth motion fidelity, reduce excessive optical
stretching without global-current sliding, reconcile local gradient normals,
current-map performance and guided rejoin; whole-river scenery and subsequent
rivers/crew/release/commit remain open. The [expanded flow-domain correction](full-river-expanded-checkpoint.md)
continues separately and is not promoted into runtime.
