# Distant checkpoint terrain fragments: rendering controls

September24 bounded diagnosis; no scene fix or acceptance.

The normal checkpoint replay in [water scenario reset](water-scenario-reset.md)
shows separated terrain-shaped patches above the distant ridge at phase1-3.
Two fresh ephemeral controls repeat the same normal-start checkpoint/return:

- `south-fork-checkpoint-no-hlod-v1-20260924`: extra command
  `wp.Runtime.HLOD 0`. Engine source `HLODRuntimeSubsystem.cpp` defines this as
  disabling HLOD loading/rendering and updates loaded-object visibility. Command
  is present in launch/log, with no unrecognized-command error; this run does not
  export the subsystem's final enabled Boolean, so do not overstate state proof.
- `south-fork-checkpoint-no-nanite-v1-20260924`: extra command `r.Nanite 0`;
  runtime log explicitly confirms `r.Nanite = "0"`.

Actual1280×720 phase1-3 PNGs from both controls were inspected. The separated
patches remain above the same ridge, with the foreground raft/water/terrain
present. Neither control resolves the visible defect. This points the next
investigation toward identifying the actual components/meshes at those screen
positions and inspecting source connectivity, transforms, bounds and residency.
It does not yet prove a specific mesh-generation or streaming fault.

Both native checkpoint reports pass wet contact and progressing detail after
relocation/return, engine exits0 without timeout. Their report SHA256 values:

- HLOD-off: `ddcd5ec1f1de4c6b9de119d6d3bc6c26c837849a8cf279717c7abcc61249316e`.
- Nanite-off: `de2d68d1879fda640e0319001eb1ad53ee8f39914837682f494d8ad52f546025`.

Reports, process identities and per-image hashes are in
`unreal/Saved/RaftSimValidation/` under the labels above, ending in
`-checkpoint.json` and `-process.json`. Images end in
`-checkpoint-phase-1-3.png`; logs with matching labels are in `unreal/Saved/Logs/`.
The HLOD-off log also retains HLODBuilderInstancingSettings import warnings;
their causal relationship to these fragments is not established.

No saved map/mesh/source/material or normal rendering setting was changed.
Do not promote either diagnostic toggle as a fix. No cost profiling or new
physical/visual acceptance was performed. Original cook36692 was guarded and
resumed; no duplicate cook was started. Continue South Fork before queued rivers.

## Owner-ray isolation

The opt-in `-RaftSimCheckpointTerrainRays` checkpoint observer now records seven
read-only complex visibility rays at each destination capture, including camera
origin/direction, collision misses and hit actor/component/mesh/transform/bounds.
It uses normalized screen locations from the1280×720 evidence. It neither moves
terrain nor changes collision/render state. A collision ray is not a GPU pixel-ID
buffer: a hit can be behind visible geometry, and a miss is retained as a miss.

Editor build45.74s succeeds (`tmp/checkpoint-terrain-rays-editor-v1-20260924.log`).
Normal-rendering replay `south-fork-checkpoint-terrain-rays-v1-20260924` passes
wet-contact/detail progression and exits0; original phase1-3 image is inspected
and still shows the fragments. Report SHA256:
`8c082279980cb5234c9be58b9dad8c2ad85c2bcf3f21f7aa9dcd07505442a73f`.
Reports/images/process receipt use the same directory/suffix convention above.

At phase1-3, rays through(600,207),(620,210),(900,268),(890,275) all hit
`/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/ContextTiles/SM_SouthFork_context1024_2560_2560`.
Distances492.927–900.244m; component translationcm(-1452200,-142800,0),
scale(1,-1,1), zero rotation. The ridge-below ray(600,240) instead hits
`/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Tiles/SM_SouthFork_coarse_2432_2816`
at403.149m. Rays(840,270) and(900,305) miss collision.

The context source is
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/source_context_extension/render_tiles_1024m/context1024_2560_2560.npz`.
`prepare_south_fork_context_tiles.py` exports only supplemental quads; it does
not provide a complete rectangular terrain tile. The source manifest asserts
additive/non-overlapping topology and retained original coarse triangles.
Consequently the next check must distinguish an actual source-coverage gap from
complementary original tiles absent in runtime residency. Do not join fragments,
move captured heights or hide the context mesh merely to mask the symptom.
Source connectivity, matching original coverage and actor residency still need
qualification; no precise cause or terrain fix is claimed yet. Cook36692 remains
the sole live job. No standalone Game rebuild or performance claim for this
opt-in observer-only addition; normal gameplay behavior is unchanged.

## Source-topology follow-through

Read-only NumPy inspection of the identified context NPZ and both topology
archives narrows the next residency check. The extension topology SHA256 is
`2a7535dea7d53ac82bf3234193423b16770a4cbd8e0bbba637e81dfdfa2855ef`.
Mapping each triangle's source-grid indices through the10006-column grid gives
exactly4483 unique quads, each with two triangles; all belong to the supplemental
mask. This equals the supplemental-mask count in the tile's512×512-quad footprint.
The export therefore does not omit any supplemental quad in that footprint.

Of262144 footprint quads,79068 belong to the combined terrain mask:4483
supplemental and74585 original. The other183076 are outside that mask. These
counts describe source coverage, not visible pixel holes or runtime residency.
Across the four cardinal edges of every exported quad,16853 neighbours are
supplemental,511 original, and568 uncovered. All511 original neighbours match
the retained original topology after applying the extension's71-column offset.
The complementary original mesh names and shared-edge counts are:

- `coarse_2432_2816`:1
- `coarse_2560_2816`:94
- `coarse_2560_2688`:98
- `coarse_2688_2688`:86
- `coarse_2688_2560`:96
- `coarse_2816_2560`:51
- `coarse_2816_2432`:57
- `coarse_2560_2432`:28

Next inspect these exact eight components' runtime residency/visibility and
project the combined source coverage into the checkpoint camera. In particular,
the ridge-below ray already hits the first mesh, so absence of *all* original
terrain is not a supported explanation. This does not yet distinguish legitimate
outer coverage boundaries from missing complementary visible terrain. Do not
fill the uncovered footprint with invented source heights. No engine rerun,
asset change, new frame-cost measurement or playable improvement is claimed by
this bounded source check. Sole cook36692 remains live; no duplicate was started.

## Actual runtime residency and range control

The same opt-in observer now enumerates loaded static-mesh components for the
nine identified mesh names, retaining empty matches explicitly. It records
registration, visibility, actor-hidden state, render-state creation, recent
rendering, transforms and bounds. Empty matches prove only absence from the
current runtime world, not missing saved actors or packages. Editor build
`tmp/checkpoint-terrain-residency-editor-v1-20260924.log` succeeds in34.25s.

Normal-default replay `south-fork-checkpoint-terrain-residency-v1-20260924`
finds only the context mesh and `coarse_2432_2816` loaded in all four destination
captures; both are registered, visible, not actor-hidden, have render state and
were recently rendered. The other seven complementary meshes have zero loaded
matches throughout. Inspected phase1-3 still shows both floating patches.
Report SHA256 `87aa888809d7e0bb7f6cd0fb87ecd784f0cbb1272f633ce1bdbbadf552880342`.

An ephemeral control, `south-fork-checkpoint-terrain-range-v1-20260924`, requests
`wp.Runtime.OverrideRuntimeSpatialHashLoadingRange -grid=0 -range=200000`.
Installed engine source defines the command and the launch/log records it,
but the observer does not yet export actual hash type/grid/range. The command
must therefore NOT be represented as a verified2km active loading radius.
The final capture has the same loaded/absent meshes and visible fragments.
Report SHA256 `4090e17324585c2c70ca3827346729c1c6633546cb462151522a32c7f9ca5fda`.

Both runs pass checkpoint wet-contact/detail progression, exit0 without timeout,
and guard/resume cook36692 successfully. No saved map/configuration or terrain
geometry changes; no new FPS measurement. Next inspect actual runtime hash/grid
configuration and saved descriptors for the seven absent actors before repeating
a range experiment or changing normal residency. Source export manifests do
contain `coarse_2560_2816` and `coarse_2560_2688`; runtime absence alone does not
prove that either was placed in the saved map. This remains diagnosis, not a
playable fix or river acceptance.

## Saved-map correction

`audit_south_fork_checkpoint_terrain.py` loads the nine exact saved actors without
saving. All are present, spatially loaded, not editor-only, visible and not hidden,
with expected meshes/transforms and default runtime-grid assignment. Map and
selected actor-package hashes are unchanged. Its report is
`south-fork-checkpoint-saved-terrain-v1-20260924.json`, SHA256
`8e9c861518715513e94f136bde2cb5200d2ceb621993002b3dda7dd5314b5225`.

The runtime observer now records the actual hash class and reflected partition
configuration. `south-fork-checkpoint-terrain-hash-v1-20260924` proves the map
uses `WorldPartitionRuntimeHashSet` with `MainPartition`, not the spatial-hash
grid configured in DefaultEngine.ini. Report SHA256
`bda1306a12318fd12d9c8142ab8eec2f91ca0f7cf1f3281b0aabef5fbbbfb513`.
Editor build37.59s succeeds. This explains the prior wrong-hash control's lack
of effect; do not repeat it as a test of this map's active loading range.

Correctly targeted control `south-fork-checkpoint-mainpartition-range-v1-20260924`
uses `wp.Runtime.OverrideRuntimeLoadingRange -grid=MainPartition -range=200000`.
All nine meshes now have loaded matches. Inspected phase1-3 shows continuous
terrain at both former floating-patch gaps. Report SHA256
`8be14c98e1ac26bab6f2990ab8ef4852921f64fe7fcd486cc65c47d70a54f3e6`.
The attempted `south-fork-mainpartition-range-cost-v1-20260924` cost run contains
two separate ExecCmds arguments; it is NOT accepted as verified candidate cost.

`fix_south_fork_terrain_loading_range.py` applies the same range to the saved
South Fork MainPartition only. It gates on the exact inspected map hash,
partition identity and old range, backs up the map before editing, and saves no
source meshes, captured data, actor transforms, hydraulic fields or other maps.
Actual saved range was25600cm, now200000cm. The initial two script attempts
failed protected/snake-case property reads before backup/mutation; their logs
`south-fork-terrain-range-normal-v1`/`v2-20260924.log` are retained. Exact reflected
property names succeed in `v3`. Mutation receipt:
`south-fork-terrain-range-normal-v1-20260924.json`.

- Old map SHA256: `c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`.
- Saved map SHA256: `27a67b3d6de5ba88b38d43ec527cc90acd2524f8d646278fc013c433ced0376f`.
- Recoverable backup: `unreal/Saved/RaftSimValidation/south-fork-terrain-range-before-v1-20260924.zip`, SHA256 `171486d37da2819ff26018c09d4deb3ddacd8f758fd15deed2b70d5e004f5d3f`.

Fresh normal-default replay `south-fork-terrain-range-normal-checkpoint-v1-20260924`
has NO loading-range override. It passes checkpoint wet contact/detail advance,
exits0 without timeout, and its inspected phase1-3 shows both former gaps closed.
Report SHA256 `3341741eb5b52d57143f3f4793733ffb6b80d909b000cff9bc26befec1f632c2`.
This is an incremental normal-scene terrain fix, not full-route geometry,
shoreline, water realism, motion, sustained performance or river acceptance.
All guarded replays resume the original cook36692; no new cook is started.

Normal-default900-frame cost capture `south-fork-terrain-range-normal-cost-v1-20260924`
has no extra startup commands; FrameTime mode is confirmed, scope offset1.
Rows60–840: mean24.025367ms, p9532.8845ms, maximum51.246ms: short first-pool gate
PASS against33.333333ms, not full-route or corrected-destination performance.
CSV SHA256 `553cdc8b3540dcd8c050bdd6d8cd2d02e43d6732e30aa704913c094abca1747b`;
audit `tmp/terrain-range-normal-frame-v1-20260924.json`.

Game build initially fails closed on the expected stale map hash in the runtime
bundle (`tmp/terrain-range-game-v1-20260924.log`). A fresh read-only native reload,
`audit_south_fork_terrain_range_bindings.py`, verifies saved MainPartition range,
unchanged water/route actor bytes and entrypoints. Binding report
`tmp/terrain-range-saved-bindings-v1-20260924.json` has SHA256
`8f0a1bb9cfbdd8a3a2206851fc4b9f53cc31877c76db612feb7f504ddad7d925`.
`rebind_saved_map` verifies all2405 payload files and complete unchanged actor
inventory before updating only the map and native-binding hashes in the bundle.
This is a required map-only packaging dependency update, not rebasing historical
visual evidence or blessing different hydraulics.
Game rebuild succeeds in75.95s (`tmp/terrain-range-game-v2-20260924.log`), and
`physics/tests/test_runtime_data_bundle.py` passes38 tests in3.61s. This proves
build/dependency consistency, not freshly packaged execution. Full temporal
terrain review and corrected-destination/full-route performance remain next.
