# Unmasked total-depth source in normal South Fork — September 13

The previous turn made progress by bridging completed GPU frames into the
existing shared presentation queue. This turn connects the live mean/source
input path, which previously discarded sub1cm water and only collected paired
bed/carrier geometry for explicit diagnostic captures.

## Runtime implementation

Normal moving Cartesian detail now builds an immutable source packet from the
same65x65 live samples used by its existing mean update. It keeps positive
depth independently of `bWet`, the old1cm detail cutoff and rounded absolute
surface-minus-bed. Velocity is rotated into the same fixed east/north basis
before forming momentum. Bilinear interpolation operates on h/hu/hv, not on h
and velocity separately. The packet includes exact paired sampled bed/carrier
values, origin, cell size, sample time and a monotonically increasing revision.

This is point-grid interpolation of sampled quantities, NOT a conservative
finite-volume remap or newly measured bathymetry. Existing captured/inferred
bed provenance remains unchanged. The source has zero transported-foam density
because the field sampler supplies no such quantity; it must never reset foam
or overwrite h/M in retained evolving cells.

The render-thread source owner uploads each new immutable revision once into
three persistent GPU buffers (state, physical bed, reference). Repeated render
commands for that same packet do not allocate/upload it again. Regressed or
unpaired revisions fail without replacing the retained packet. No CPU readback
or GPU wait is added to normal play. This path is unconditional for moving
Cartesian detail: no snapshot or solver-research flag is required.

The existing playable detail solver still receives its original inputs and
continues evolving as before. The new source buffers are ready for the total-
depth owner and entering/open-boundary inputs; this is not permission to copy
the sampled mean over the evolved interior at every update. Total-depth live
interval ownership, physical open boundaries, conservative window exchange
and breaking/foam evolution remain unfinished.

## Native verification

Build12869 succeeded69.54s. Actual-D3D12 regression20205 CLOSED74clean passes,
zero warnings/failures/unrun,15.731615s:
`unreal/Saved/RaftSimValidation/south-fork-live-source-regressions-v1-20260913/index.json`.
The new `RaftSim.WaterDetail.LiveTotalDepthSourceGPU` test verifies:

- 1e-30m depth survives when rounded bed and surface both equal1000000m.
- Presentation-dry0.005m water is retained.
- A depth2/10 and velocity1/3 midpoint has h6 and hu16, not the incorrect hu12
  produced by separately averaging depth and velocity.
- Invalid depth, velocity, carrier, paired sample dimensions/depth or revision
  is rejected; no clipping or replacement water is introduced.
- All16,384 state/bed/reference cells upload bit-exactly to the actual GPU.
- Same-packet upload deduplicates; stale revision fails; a later moved packet
  leaves the previous immutable origin/time intact.

Raft DLL SHA256:
`c367a1f26c8456463e35606364d3477410b93ebdf5185d4b2d7d885f21d08b7b`.
Source-builder header SHA256:
`e00f359b18cbb0857d2c15cfb14c1dda7cec327c5d1c31f2aaeabe77d2a9d468`.
Source-uploader header SHA256:
`b0777257adda26a9d1d5cd154da9e8b67084f437fb8193421fa70d120d9c8f0f`.
No CPU PDE or new long replay this turn; previous numerical evidence keeps
its recorded implementation hashes and limitations.

## Normal launch and first cost measurement

Normal profile39084 CLOSED exit0. Verified cook29104 suspend/resume both return0;
no restart or replaced process. Standard1280x720 D3D12 FullReach scenario launch,
same quality/physics settings, no snapshot or total-depth research opt-in:
`unreal/Saved/Logs/south-fork-live-total-source-v1-20260913.log`.
Live source confirms235uploads/revision236,16,384cells and950 positive depths
at or below1cm in the final packet. Mean preparation236updates,2.118009ms
average/3.025800ms max. Seven exact detail remaps, zero teleports,656 paired
presentation commits/1hold, simulation34.008335s and backlog0.008032s.

CSV `unreal/Saved/Profiling/CSV/south-fork-live-total-source-v1-20260913.csv`,
SHA256 `ade1051cf613f43c157ad1679508275d6eeefff393ef6fb9850361ca193acd11`.
Report `tmp/south-fork-live-total-source-performance-v1-20260913.json` uses
rows60–240 inclusive:20.661446FPS/p9566.1661ms, FAIL30FPS/33.333ms.
Game-thread mean48.157931ms, GPU15.281482ms. Nested shoreline SetMesh18.520381ms,
crest update14.238183ms and selection7.051993ms must NOT be added together.
Same rows of the retained indexed baseline score21.565765FPS/p9552.775ms;
comparison report `tmp/south-fork-live-total-source-comparison-v1-20260913.json`.
Trajectories/refresh timing differ; these runs do not isolate source-upload cost
or establish a causal regression/improvement. Both fail the target.

Actual screenshot was inspected:
`unreal/Saved/Screenshots/south-fork-live-total-source-v1-20260913.png`, SHA256
`0753864967413f625be7e514a53759fabc5162cfabc89d6694852dff81a897d3`.
Broad smooth glossy crests and extensive soft white patches remain visually
unaccepted. A still frame is not continuous breaking-wave motion evidence.
Map/material/save hashes remain unchanged after play.

Inspection exposed redundant geometry work in v1: the ordinary path generated
both the new packet's bed/reference and a full diagnostic geometry copy. v2
keeps coarse paired live samples unconditional but creates the duplicate
resampled capture array only when a capture is actually requested. Source
values and evolving solver inputs are unchanged. Build52058 succeeds14.86s;
v1 evidence retained. Current Raft DLL SHA256:
`8cd278dc000efad9428d97df1f1a492f6c4e1900f4592d0b8257fb9e267e2db0`.
Final native26647 CLOSED exit0:74clean passes, zero warnings/failures/unrun,
16.011993s; `unreal/Saved/RaftSimValidation/south-fork-live-source-regressions-v2-20260913/index.json`.
Scoped tracked whitespace checks pass; no release/whole-worktree acceptance or
commit is claimed.

Second normal profile73179 CLOSED exit0; same cook suspend/resume status0.
`unreal/Saved/Logs/south-fork-live-total-source-v2-20260913.log` confirms240
uploads/revision241,1,082 positive sub1cm cells,241mean preparations averaging
2.007680ms/max2.861600ms,745presentation commits/1hold and0.008208s backlog.
The duplicate-work change is real, but its roughly0.11ms-per-update difference
cannot explain the full frame-time change; no causal FPS gain is claimed.

Final CSV SHA256:
`180268d4fa7441fa17c86981f7df587b58c588be2a36ada36c4ac8fa0645a51c`.
`tmp/south-fork-live-total-source-comparison-v2-20260913.json` compares identical
rows60–240 of all three retained captures. v2 measures23.365478FPS,
p9547.2488ms, game thread42.648937ms and GPU14.660522ms: STILL FAIL30FPS.
Different trajectories/refresh work remain confounders. Both screenshots were
inspected; v2 is a different boat position/view, not evidence of new water shape.
`unreal/Saved/Screenshots/south-fork-live-total-source-v2-20260913.png`, SHA256
`faaf73227cdb38c23d7894d3557e64237a74080f17e95d6ea689854d820e5934`.
Smooth glossy crests and broad soft foam remain unaccepted; no continuous
recording or reference-video playback was performed. Map/material/save hashes
remain unchanged after both ordinary-play launches.

Cook96057/PID29104 verified live again after both profiles,3757.5s/local35150.
Latest independently audited3700s/local34000 remains finite with artificial
banks dry but flow unsettled. Next3800/local36000 requires both audits after
complete marker. Runtime fields remain600s; no cook/field promotion occurred.

## Acceptance boundaries

The source packet/upload is a normal-game integration, not a visible breaking-
wave/froth delivery. No scene or30FPS acceptance follows from the74test result.
Quality, resolution, physical timestep, solver/memory budgets and geometry/
contact gates remain unchanged. South Fork remains the scenario; Troublemaker
stays off-menu. Terrain/rapid reconstruction, full live new solver integration,
all later rivers, crew, release and final commit remain open.
