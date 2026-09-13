# South Fork playable current detail — September 12, 2026 UTC

An incremental material improvement is now installed in normal gameplay.
South Fork reconstruction, physical whitewater and release acceptance remain open.

## Delivered change

The startup menu's South Fork and Troublemaker entries use
`/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`. Its existing single water
surface selects `M_RaftSim_SouthForkRaftTransmissionWaterV4`. That actual saved
parent now uses triangular gradient normals translated by the existing
`RaftSimFoamAdvectionMeters` current displacement. Pixel-footprint filtering
fades unresolved detail. No review flag or alternate map is required.

Actual guide-camera images at station 8320 m now show smaller irregular ripples
and reflected patches instead of the former broad smooth pale bands. The
12-frame rest/drift sequence spans world time 10.333832–13.051221 seconds;
logged raft speed changes from 0.88 to 0.85 m/s. First and last frames were
visually inspected. This short sequence does not qualify long-run temporal
stability or prove exact raft/foam velocity agreement everywhere.

This changes optical detail only. It does not install the captured terrain,
repair the rejected liquid solver, add breaking-wave geometry, or establish
convincing froth. Some distant smooth bands and coarse near-field facets remain.

## Verification

- Editor build session19870 completed successfully in 1106.86 seconds. Initial
  build71556 was deliberately stopped after 13 actions for slow scheduling;
  completed objects were retained. The successful build used
  `-NoUBA -MaxParallelActions=4`.
- `unreal/Scripts/review_south_fork_current_normals.py` ran successfully in
  actual Unreal (session41968). It verified the saved normal connection,
  integrated-current inputs and pixel filtering. All 80 existing scalar
  constants and the base-colour, roughness, opacity, opacity-mask and WPO
  connections remain unchanged. Repeating the refresh adds no nodes
  (681 expressions). Shader compilation and saving completed.
- Sixteen existing optical regression functions passed, including independent
  finite-difference verification of the triangular gradient. One unrelated
  existing assertion requiring exactly six water-upload calls fails; its
  runtime source was not modified by this change. These were invoked directly
  because the available Python environment lacks pytest.
- The normal-game baseline and updated runs both contain pre-existing engine
  Python startup errors for `AgentSkill` and `PythonTestRunner`. Gameplay still
  completes. Do not describe the whole project or logs as error-free.

## Matching short performance measurements

Both runs used the actual FullReach game scene, station 8320 m, 1280×720,
87% screen percentage, ten seconds warmup and twelve seconds sampling.
No screenshot writes occurred during either measurement.

| Measurement | Original | Updated |
| --- | ---: | ---: |
| Sampled frames | 455 | 470 |
| Mean frame work | 26.463 ms | 25.562 ms |
| P95 frame work | 43.758 ms | 40.826 ms |
| Mean GPU | 9.228 ms | 9.063 ms |
| Mean wall-clock frame | 26.409 ms | 25.602 ms |

There is no measured slowdown in this short pair. This is not a statistically
established performance improvement. Both fail the 16.667 ms target and are
explicitly offscreen engineering diagnostics, not packaged release qualification.

## Artifacts and recovery

All paths below are relative to the repository:

- Original capture: `unreal/Saved/Screenshots/southfork_playable_baseline_20260911_2310_000.png`.
- Updated captures: `unreal/Saved/Screenshots/southfork_playable_current_normal_20260912_000.png`
  through `_011.png`; matching log in `unreal/Saved/Logs`.
- Asset audit: `unreal/Saved/RaftSimValidation/southfork-current-normal-20260912.json`.
- Performance reports: `unreal/Saved/RaftSimValidation/southfork_current_normal_baseline_perf_20260912.json`
  and `southfork_current_normal_updated_perf_20260912.json`.
- Saved parent SHA256: `135ec9cf2c21adc7a25b5121ff1d3eb79f6968dc612c14ca3206166e3d7f8d1c`.
- Original parent backup: `tmp/southfork-water-v4-before-current-normal-20260912.uasset`,
  SHA256 `2471423a5970eb7543ff9731a2b80795ee039e17c24fec65024fd29e5b2f8344`.
- Scoped refresh command: `RaftSim.RefreshSouthForkCurrentNormals`.
  The ordinary South Fork material authoring path also retains this normal.

All runs are terminal. No map file, solver, captured-source geometry or later
river was changed. No shipping package, final commit or queue completion is
claimed. Next work must keep delivering through the normal scene: resolve its
missing froth/rapid shape and integrate consistent reconstructed geometry,
while preserving the rejected solver's physical gates.
