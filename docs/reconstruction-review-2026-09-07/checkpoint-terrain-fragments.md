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
