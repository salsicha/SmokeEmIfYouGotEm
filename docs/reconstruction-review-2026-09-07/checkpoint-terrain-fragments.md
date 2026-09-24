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
