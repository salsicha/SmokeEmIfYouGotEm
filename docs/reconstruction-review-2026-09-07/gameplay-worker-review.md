# Eight-worker gameplay review: not promoted

2026-09-17. The offline cook's qualified eight-worker speedup does not establish
a gameplay speedup. The temporary dual-flag startup control committed in
`7c785ede2` was tested and removed. Normal gameplay retains four maximum lanes,
including the caller. The separately qualified offline cook still uses eight.
No solver equations, timestep, tolerances, terrain, water state or assets changed.

## Build and comparison controls

The first editor link failed because the installed native archive lacked the
existing worker-configuration symbol. Rebuilding that archive resolved the link;
the full editor build completed all 163 actions successfully. Archive SHA256:
`c18e0a458cffb6218fecc7da68e3ad4c73c48c37a0791a171fbb6dce16352344`.
The same completed build was used for every four/eight comparison; no partial
DLL set was launched. Build logs are `tmp/solver-eight-gameplay-build-v1-20260917.log`
(failed) and `tmp/solver-eight-gameplay-build-v2-20260917.log` (succeeded).

Every run uses normal South Fork FullReach, FullDescent, review station 8330 m,
1280x720 D3D12, Development, WindowsEditor, 300 CSV frames, and inclusive rows
60..240. There is no joint-preview state, video recording or quality reduction.
The eight-lane marker is required only in eight-lane logs. Cook PID6968's exact
start/executable identity is checked and retained handles suspend/resume it
around each run. All eight comparison processes exit zero without timeout;
all suspend/resume calls succeed. The second set's first process CPU accounting
advances 0.125 seconds between the pre-suspend and pre-resume readings; other
comparison readings are unchanged. These short shared-host runs are not a
sustained, packaged or full-traversal acceptance test.

The first complete 4/8/8/4 sequence is preserved but INVALID as a comparison:
eight-b has duplicate `LightCount/UpdatedShadowMaps` and `ShadowCacheUsageMB`
headers. Local UE source identifies these as renderer counters. The auditor's
duplicate-header rejection was not changed and the CSV was not rewritten.
The other three captures are retained only as an explicitly incomplete diagnostic
in `tmp/solver-eight-gameplay-incomplete-v1-20260917.json`; all three fail30.
A complete fresh 4/8/8/4 sequence was then run with unchanged settings, not just
a replacement of the missing result.

## Valid complete comparison

| Fixed order | Average FPS | Mean frame ms | Frame p95 ms | Mean solver ms |
| --- | ---: | ---: | ---: | ---: |
| Four A | 28.988918 | 34.495940 | 41.5534 | 5.748542 |
| Eight A | 30.372921 | 32.924065 | 42.9884 | 4.276086 |
| Eight B | 30.686702 | 32.587405 | 41.7355 | 4.055034 |
| Four B | 30.072383 | 33.253102 | 41.8105 | 5.492593 |

Eight lanes reduce solver and mean-frame time in both pairs, but p95 worsens in
the first pair and barely improves in the second. Every run exceeds the unchanged
33.333333 ms p95 limit. This is not a repeatable frame-consistency improvement or
a 30 FPS pass; the gameplay control is removed rather than promoted. Do not
conflate this decision with the separately verified full-river offline benefit.

Report: `tmp/solver-eight-gameplay-abba-v2-20260917.json`, SHA256
`ca3ac90128c37c00ba939ec4010572df14e6001850fcd00b9a1531fcbee1b780`.
CSVs under `unreal/Saved/Profiling/CSV/` use
`south-fork-solver-lanes-<case>-v2-20260917.csv`:

- four-a: `0fc046cff4d35a045bf08e265ae6ae95fea224d879ade45d8283a6f5078f38e5`
- eight-a: `9d8a09c9ea73d38de4dfe1799d3c70ae4b79cfa1b6557b28d50b8617af4d4702`
- eight-b: `caa3c0ecaec13e939dee95188915a1052e0bd80d25231652f7c4648522eabea4`
- four-b: `1206ecf63218b9cea470ccbd335e1e206f4237e2f526fdd150cf7e0cd7376561`

## Restored installed runtime

The startup source matches `cefd5aa12` exactly; no experimental flag remains.
The four-action restoration build succeeds. Installed Water DLL SHA256:
`9eb45743c1c0318ce61fe75a53cbe7ecc638f2ef7a11d5876a3d4a1b56fd95fb`.
Six fresh native tests pass with no failed, warning, skipped or in-process tests:
SharedCartesianAtlas, ShorelineCapturedGroundRendering, ShorelineTerrainProbe,
SurfaceSourcePacking, ShorelineExactCache and ShorelineMovingBankCache.
Report: `tmp/solver-four-restored-native-v1-20260917/index.json`.
All 35 frame-auditor, reconstruction-launch and terrain-replacement Python
tests pass. This focused group does not close the existing broader regressions.

The final restored normal profile exits zero, records all 300 frames, and resumes
the cook successfully with unchanged CPU accounting during the measurement.
It averages **27.726765 FPS**, mean **36.066235 ms**, p95 **43.0055 ms**: still
**FAIL30**, not an accepted baseline. CSV SHA256:
`b9bbd1bc6bc44aa051225e54f7aa38a31765a78044f70fca3640a43dcaba06dc`.
Report: `tmp/solver-four-restored-profile-v1-20260917.json`.
This is a fresh measurement, not proof that the restoration caused the difference
from earlier runs. No new visual acceptance is claimed; the previously observed
broad soft froth, rock-detail and vegetation limitations remain.

## Hydraulic dependency and remaining work

The 5350 s / local9000 checkpoint independently passes all 5,382,400-cell state
checks and all 86,720 artificial-bank cells remain exactly dry. Depth maximum
3.701844632 m, speed maximum 6.190027316 m/s; maximum per-step conservation
residual 1.522912418e-8 m3. Outflow **119.970991** versus inflow **45.306955** m3/s
is not settled. Depth-array SHA256:
`41048f2ec818394a1eae01eaeea567c2a96b71960c981984fc778b44c0c61d98`.
Reports: `tmp/control-ablation-5350s-state-v1-20260917.json` and
`tmp/control-ablation-5350s-banks-v1-20260917.json`.
Only the verified 4950 s state remains installed. The same cook continues toward
5400/local10000, which requires a completion marker and both audits before any
continuation or use. Later checkpoints are not silently installed.

Source-consistent terrain/flow, physical breaking and convincing froth, contact,
motion, sustained performance and release remain open. Continue South Fork,
then Colorado, Pacuare and Futaleufu, with Chilko/Zambezi, crew, normalization
and broader regressions retained in the full queue. Troublemaker stays a rapid
inside South Fork, never a separate menu scenario.
