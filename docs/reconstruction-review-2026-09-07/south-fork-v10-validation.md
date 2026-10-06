# South Fork v10: correctness passed, performance and appearance unfinished

September29UTC. No normal-play delivery or whole-river acceptance is claimed.
The stored signed-neighbor optimization is exercised in the candidate only.

## Qualification and actual motion

`tmp/certified-bank-endcap-transition-v10-20260929-process.json` completed:
21/21 native tests,62 original captured states,15 exact stored polygons,
48 exact shared crossings. Tests compare original-policy and optimized outputs
including points,bounds,triangles,proof statistics and fallback counts.
ReceiptSHA256 `d988719bf1d8d38d6738ecb1585fc5a4b84cbad4c200f7926c95dd4309df33c7`.

`tmp/certified-bank-endcap-transition-live-v4-20260929-process.json` completed
with unchanged sources/binaries,engine exit0,90 samples from8312.000 to8411.484m,
586 accepted nonempty shoreline updates and zero rejected updates.
Matched presented detail49:4226GPU probes,maxRGBAerror1.4901161193847656e-8;
1902wet CPU probes,zero missing/ground-occluded points,maxsupporterror
4.765929213590425e-5cm. One contact snapshot is not swept collision or traversal.

## Isolated actual Boot/menu timing

The other owner's Lava Canyon game31800 and PIE25068 prevented initial launch.
No run was terminated. A60s idle-window scheduler then invoked the profiler once;
all source/binary checks and34workload-isolation polls passed.
Session60104 is terminal0; its exit status means measurement completed, not
that the performance target passed.

Receipt: `unreal/Saved/RaftSimValidation/sf-certified-endcap-v10-menu-20260929-frame-audit.json`.
CSV: `unreal/Saved/Profiling/CSV/Profile(20260928_232906).csv`.
CSV SHA256 `6c3a1a2a65602cdf10211c7df71f56235e622f573b60a41282061359bed130f7`.
Editor-hosted1280x720,D3D12,candidateON; real Boot/menu, no quality/solver override.
1200frames,rows30..1169audited,zero runtime errors/rejected banks.

| Metric | v9 | v10 | Required |
| --- | ---: | ---: | ---: |
| Mean frame ms | 62.796 | 52.555 | diagnostic |
| p95 frame ms | 102.2014 | 71.0396 | <=50 |
| Maximum frame ms | 442.031 | 358.8225 | diagnostic |
| Frames above100ms | 67 | 1 | 0 |

Both timing gates still FAIL. Separate runs are not paired same-state proof
of the optimization's causal speedup. Bridge debt went0.8566->0.006494s,
max0.8566s; this does not grant simulation-capacity acceptance.

Hash-checked scope comparison: `tmp/sf-v9-v10-scope-comparison-20260929.json`,
reproducible via `tmp/compare-v9-v10-scopes-20260929.py` (preserves existing output).
v10 inclusive topology mean15.494ms,p9536.9391ms,max256.1735ms; SetMesh
mean20.755ms,p9546.141ms;surfaceTick mean32.703ms,p9549.592ms.
Scopes nest/overlap across threads: do not sum them.

## Actual views

Video `unreal/Saved/VideoCaptures/RaftSim_20260928-232424.mp4`,SHA256
`6185fffb435822b8390e7d347eb141b033688b3f04d8bc42136af4788ce438ca`.
Decoded2874frames,PTS0..95.766667s,232exact adjacent duplicates.
Recording cadence is not gameFPS. Decoder ran AFTER the performance process
exited. Local visualization folder `south-fork-v10-motion-review-20260929`
under this task contains the manifest and extracted frames.

Inspected20/21/60/80s frames: raft and banks move relative to one another,
foam outlines and spray change. Broad opaque white patches still appear flat;
wispy vertical plumes occur over the raft/interior. Prominent right-bank and
boulder silhouettes remain angular. Crew/paddles show similar resting poses;
these sparse views are not a complete stroke-cycle validation.
No convincing breaking-roller/recirculation,temporal shoreline,geographic match,
full collision or crew-fit acceptance follows from these observations.

The prior normal-scene selected-site capture in
`breaking-profile-datum-and-shape.md` already establishes that a downstream
hydraulic rise can exist in both raw and submitted geometry. Do not call the
small additional analytic crest the whole wave height,or blindly amplify it.
Next appearance work should identify flat-foam/spray causes and trace submitted
shape and source ages only where the existing evidence leaves a specific gap.

Normal v27 remains unchanged,candidateOFF,broken solverOFF,no push.
