# South Fork water-normal / reflection isolation

September 17, 2026. Continuation classified as progress: new rendered-buffer,
reflection and timing evidence changes the next action. **Not scene acceptance.**
No water geometry, terrain, material asset, installed module or rendering default
was changed by these controls. Troublemaker remains a rapid within South Fork.

## What the controls establish

All preview labels below have prefix `south-fork-control-ablation-3350s-` and
suffix `-20260917`. They use the same source-paired descriptor
`tmp/control-ablation-3350s-joint-preview-v1-20260917.json`, SHA256
`9c06666f5c0ff9dbb71c061f09bdeb0ad99fd2e6aed5080db3b2c69fc20eebab`.
Each completed 24 actual 1280x720 PNGs, exited 0 and resumed the exact owned cook
with status 0. Logs/process reports/images remain under `unreal/Saved/`.
Different frame times produce different raft trajectories: these are not
pixel-registered A/B views. Visual statements below concern inspected frames,
not every frame or calibrated physical motion.

| Label middle | Explicit control | Inspected result |
| --- | --- | --- |
| `carrier-index22-v1` | indexed CPU shape/camera export | Rectangular shading patches remain in PNG 022. |
| `no-reflection-control-v1` | `r.Water.SingleLayer.Reflection=0` | Dark, flatter water; obvious patch absent in 022, but essential reflected detail is removed. Not a fix. |
| `full-reflection-composite-v1` | `r.Water.SingleLayer.TiledComposite=0` | Patches remain in 022. |
| `conservative-lightgrid-v1` | `r.Forward.LightGridHZBCull=0` | Patches remain in 022. |
| `fixed-lightlist-v1` | `r.Forward.LightLinkedListCulling=0` | Patches remain in 022. |
| `scene-reflections-v1` | `r.Water.SingleLayer.Reflection=1` | Obvious rectangular patches absent in 022, but conspicuous reflection noise. Not accepted. |
| `denoised-reflections-v1` | previous plus `r.Water.SingleLayer.Reflection.ScreenSpaceReconstruction=1` and `.Denoising=1` | Reduced noise in 022; residual noise in 001/012/022 and unfinished froth/crew. Not accepted. |
| `no-captures-control-v1` | `r.ReflectionEnvironment=0` | Patches remain in 022. Disabling local captures is not a sufficient correction. |
| `world-normal-control-v3` | explicit `WorldNormal` buffer visualization | Stepped patches visible in the actual rendered normal buffer (022); trace material/vertex interpolation next. |
| `precise-normals-v1` | `r.GBufferFormat=3` | Patches remain in lit PNG 022. High-precision G-buffer normals alone are not a correction. |

The current High preset forces water Reflection=2, which UE 5.8's
`SingleLayerWaterRendering.cpp` defines as reflection captures plus skylight,
**not SSR**. Mode 1 follows the scene reflection method (Lumen here). A changed
reflection response can conceal a normal defect; disappearance alone does not
prove the reflection algorithm was its source. The light-grid controls also do
not prove a mesh crack, missing tile, or particular capture-selection bug.

World-normal v1 was rejected because DeviceProfile overrides cannot set these
ECVF_Cheat controls. V2 used an unrecognized view-mode name. Both remain retained
but are **not normal-buffer evidence**. V3 uses the engine's verified
`viewmode VisualizeBuffer` followed by `r.BufferVisualizationTarget WorldNormal`.
Its process report confirms both commands and the PNG was visually inspected.
PNG 022 SHA256: `a93e7bad7a89a9008f7bb598431d6fd131e8ed3beef85676ebb55b9e9551cb49`.

## CPU observations and their limits

Commit `259608b9e` permits a guarded `-RaftSimCaptureCarrierShapeIndex=22` while
preserving the legacy first-frame option and rejecting malformed/out-of-range
or conflicting indices. Isolated native report
`tmp/carrier-index-observation-native-v1-20260917/index.json`: 27 PASS, no warnings.

`tmp/carrier-index22-rays-v1-20260917.json` records source hashes, game frame 150,
world time 11.284346 s and detail sequence 147. Pixels (1218,660) and (1240,660)
hit the same CPU triangle 25246; its slope is about 0.42 degrees and CPU-normal
versus face errors are about 0.30/0.35 degrees. These samples are inside the
registered detail domain. This is a game-thread shape/view observation, **not a
GPU fence, a pixel-normal readback, or proof of which visible pixels belong to
that CPU face**. The normal-buffer result must not be overruled by this audit.

The current material's saved normal graph in
`tmp/south-fork-paired-foam-flow-fresh-graph-v1-20260917.json` combines tangent-space
`RaftSimLocalCurrentNormal.hlsl` (UV0, UV3 optical flow, registered phase) with
bilinearly sampled detail slopes. Next isolate these contributions and the actual
vertex-buffer/tangent conversion at the rendered boundary. Do not blindly smooth
or delete physical wave geometry. Do not enable noisier reflections as a substitute.

## Motion and ordinary performance

All six recorded clips were independently fully decoded with
`unreal/Scripts/analyze_detail_motion.py`; reports and unmodified decoded 1/6/11s
frames are in `tmp/control-ablation-reflection-motion-v1-20260917/`.
Carrier-index, full-composite, conservative-grid, scene-reflection, denoised and
precise-normal clips respectively contain 471, 465, 467, 468, 467 and 466 decoded
frames. Their 30 Hz encoded timeline can repeat frames and is **not game FPS**.
Fixed rectangle image metrics are not water segmentation or physical validation.

Fresh ordinary-map CSVs contain 300 samples, no recording and no paired candidate
terrain. The unchanged audit uses inclusive samples 60..240, required water scopes,
30 FPS and p95 <=33.333333 ms. Each process exited 0 and resumed the owned cook.

| Ordinary capture | FPS | Mean frame ms | p95 frame ms | Mean GPU ms |
| --- | ---: | ---: | ---: | ---: |
| `south-fork-denoised-reflections-perf-v1-20260917` | 25.240387 | 39.619043 | 44.9878 | 14.022259 |
| `south-fork-reflection-baseline-perf-v1-20260917` | 25.427685 | 39.327214 | 48.4452 | 13.611774 |

Both FAIL. Reports are `tmp/<capture>-audit.json`. This single interleaved pair
does not establish a robust speed difference. CPU game-thread times dominate;
nested water timing scopes must not be added. No release/traversal acceptance.

## Completed cook, still not settled

The original PID 36872 completed its final local36000 / 3600s snapshot and is no
longer live. Do not try to pause/resume this old PID or restart the same output.
3550 and 3600 pass both state/conservation and all 86,720 exactly dry artificial
bank cells. Reports: `tmp/control-ablation-{3550,3600}s-{state,banks}-v1-20260917.json`.
Final depth maximum 4.081070m, speed maximum 5.449002m/s, volume 2,912,751.925027m3;
maximum step conservation residual 1.647021e-8m3. Final h SHA256:
`d2087cbe0f569866bbe03f28f109ccf546e5a2ad3a826418c55553c8b0ebdcd9`.
Outflow 88.244859 versus inflow 45.306955m3/s: **not settled or promoted**.
Any further run must explicitly continue from a validated checkpoint into fresh
outputs, with convergence/initial-storage assessment, not claim completion here.

## Code and open acceptance

The capture wrapper now offers only explicit startup `WorldNormal`, `Roughness`
and `SceneDepth` diagnostics. It rejects use as performance evidence and rejects
missing/wrong/failed debug-command confirmation. Ordinary lit capture is unchanged.
PowerShell identity/mode/log tests PASS; focused startup-motion and carrier Python
regressions: 34 PASS. Actual v3 normal capture verifies the supported runtime path.
Generated artifacts remain ignored. No default water-quality reduction was made.

Realistic single-surface breaking/froth, physical coupling, source settling,
reference motion, 30 FPS and traversal remain open. Then Colorado -> Pacuare ->
Futaleufu; Chilko/Zambezi, crew realism/animation, normalization, regressions and
release checks still remain. This diagnostic work closes none of those gates.
