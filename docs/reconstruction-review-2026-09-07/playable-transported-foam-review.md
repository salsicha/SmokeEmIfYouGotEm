# South Fork playable transported foam — September 12, 2026 UTC

The normal FullReach water now displays transported white foam patches. This
is a delivered optical correction, not completion of the reconstructed rapid.
The preceding user-explanation turn did not implement work; this continuation
revalidated the stopped processes and advanced the actual playable material.

## Evidence and change

`RaftSim.WaterMaterialProbe delay=10` ran in normal FullReach gameplay at
station 8320 m. At world time 10.018 s, the visible LiveVolumeCoreMesh held
26,065 vertices, 7,245 wet; 1,032 wet vertices exceeded 20% foam and 126
exceeded 50%. Maximum foam was 0.7412; the all-vertex mean was 0.0255.
The initial-frame low foam reading was not representative of this settled
field. Boulder wakes were active after streaming.

The old optical branch applied intensity 0.9, subtracted 0.28, then multiplied
coverage/core gain and multiple sparse lace masks. Thus existing transported
foam could disappear or become very faint. This was not missing simulation
output everywhere, and raising foam generation was not justified by this probe.

`ConfigureSouthForkTransportedFoam` now uses uploaded linear VertexColor.R
directly, one existing current-advected lace sample and a continuous optical
density response. Zero input produces zero foam; dense patches brighten while
water pockets remain open. Pixel derivatives soften subpixel lace edges.
The same coverage feeds colour, roughness, opacity and water scattering.
Appearance constants are inferred visual calibration, not measured aeration.
No speed-based foam source, second surface, new force or solver change was added.

The actual saved parent is
`/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4`.
It is selected by ordinary South Fork/Troublemaker gameplay; no review flag is
required. The normal authoring path preserves this integration. The existing
`RaftSim.RefreshSouthForkCurrentNormals` command now refreshes both optical parts.

## Verification

- Editor build51027 succeeded in 33.85 seconds (four actions).
- Final rebuild74960, including corrected refresh-command descriptions,
  succeeded in 34.62 seconds (five actions). All jobs are terminal.
- Unreal asset audit42758 succeeded. It checked all four optical consumers,
  the existing current-advection dependency, unchanged complete reachable WPO,
  opacity-mask and normal graphs, and repeat-refresh idempotence (684 nodes).
- Twelve real guide-camera frames were captured. Frames000 and011 inspected:
  new white patches appear, particularly toward the right bank; smaller foam
  detail appears around the raft. World time10.323612–13.082435 s, raft speed
  0.88–0.85 m/s. This short sequence does not prove long-run stability or exact
  local foam/raft velocity parity. All capture processes exited.
- 21 focused Python test functions pass via runpy (pytest unavailable). The
  stale six-upload regression was repaired after inspecting all seven current
  C++ sites: three SurfaceMesh, three LiveVolumeCoreMesh and one RapidFoamMesh.
  Every call already passed explicit false for sRGB conversion. The revised
  test verifies those exact owners/counts and the final argument, with negative
  tests for omitted/true/comment-only arguments. No runtime conversion behavior
  or physical acceptance gate was relaxed.

## Short performance comparison

Both runs: normal FullReach, station8320,1280×720,87% screen percentage,
10 s warmup,12 s measured, no screenshot writes during timing.

| Metric | Previous current-normal material | Transported foam |
| --- | ---: | ---: |
| Sampled frames | 470 | 467 |
| Mean frame work | 25.562 ms | 25.738 ms |
| P95 frame work | 40.826 ms | 41.841 ms |
| Mean GPU | 9.063 ms | 9.148 ms |
| Mean wall-clock frame | 25.602 ms | 25.729 ms |

No material change in cost is established by this single short comparison.
Both FAIL the 16.667 ms target. These are offscreen engineering runs, not
packaged release qualification. Known engine Python startup errors remain.

## Artifacts and remaining integration

Repository-relative artifacts:

- `unreal/Saved/Logs/southfork_settled_foam_probe_20260912.log`
- `unreal/Saved/RaftSimValidation/southfork-transported-foam-20260912.json`
- `unreal/Saved/Screenshots/southfork_playable_transported_foam_20260912_000.png`
  through `_011.png`, and matching log under `unreal/Saved/Logs`.
- `unreal/Saved/RaftSimValidation/southfork_transported_foam_perf_20260912.json`
- Recoverable pre-change parent: `tmp/southfork-water-v4-before-transported-foam-20260912.uasset`,
  SHA256 `135ec9cf2c21adc7a25b5121ff1d3eb79f6968dc612c14ca3206166e3d7f8d1c`.
- Updated parent SHA256 `06ed556dbf027e705f0d93f2def1974c2a20092ea36f9932958657bf778b5c57`.

The scene still has the old terrain/route and lacks convincing breaking-wave
geometry. The captured-source 33.334 km route, matched rock/terrain/flow and
scenario starts must migrate together. In particular, the corrected geographic
registered-rock map has sampled collision and guided-traversal evidence, but
still points at tmp hydraulic data and is not the normal menu destination.
Do not place captured geometry onto the old approximately49 km coordinate map
or silently label the bounded review a completed full descent. Resolve that
playable integration next, preserving measured/inferred provenance. South Fork,
later rivers, crew, release performance and the full goal remain incomplete;
no final commit or completed-project claim.
