# Exact render conversion installed in normal South Fork play

Recorded 2026-09-17 UTC. This is an installed CPU rendering improvement, not
convincing-water, physical-flow, sustained 30 FPS or release acceptance.

## Implementation and exact qualification

When the exact dense source membership is unchanged, render-packet conversion
now writes disjoint 1,024-vertex ranges in parallel. Each vertex still uses the
original conversion, with its current position, packed tangent/normal/handedness,
color and all four rendered UV channels. No geometry, membership, winding,
profile updates, solver steps, detail levels or error thresholds are removed.
Topology rebuilds retain the original remap/conversion. The reference control is
`-RaftSimSerialRenderValues`; the read-only paired probe is
`-RaftSimRenderValuesAudit`. Normal play needs neither option.

The original and candidate outputs were compared on all 64 actual South Fork
frames 120-183, alternating call order, with fresh output arrays and independent
mapping copies outside the timed scopes. All 1,674,036 rendered vertices match.
All frames, including eight unchanged-path topology rebuilds, remain in the
report. The candidate is faster in both call orders and in each reused-membership
subgroup:

| Group | Original ms | Candidate ms |
| --- | ---: | ---: |
| All 64 pairs | 1.036548 | 0.507145 |
| Original first | 0.976163 | 0.343522 |
| Candidate first | 1.096934 | 0.670769 |
| Reused membership, candidate first | 0.908008 | 0.323487 |

The initial candidate passes seven native tests; the final default-enabled build
passes **22 shoreline/crest native tests, zero warnings/failures/not-run tests**.
The new test covers empty/single and 1,024-batch boundaries, reversed/repeated
membership, changing heights/UVs/handedness, and exact-dry clearing. The strict
pair auditor rejects missing/duplicate/malformed frames, output mismatches,
invalid timings, absent reuse coverage and one-order-only speedups.

Final Python audit/profiler regressions: **43 passed**. The frame-CSV reader now
reports the already-recorded optional RenderPacket scope; it remains separate
from SetMesh and does not alter frame-time or p95 calculations. An initial test
launch without the existing dependency directory failed to import pytest; the
configured rerun passed. The first compiler invocation used the wrong working
directory and failed to resolve engine includes; the corrected engine-directory
build passed. Neither launch failure is counted as a test/build pass.

Evidence (generated artifacts remain local and ignored):

- Pair report `tmp/south-fork-render-values-pair-v1-20260917.json`, SHA256
  `5d9086949a6fe319d4ac66da01c3045bb0fad2a39271d0b8f40341d9b9d65d63`.
- Native report `tmp/render-values-native-v2-20260917/index.json`, SHA256
  `723bac8e282f3f8754d415958006efe5e7fc1d8d28400524c9341c9a2c6994c1`.
- Python report `tmp/render-values-regression-v2-20260917.xml`, SHA256
  `3e02202e3fffa2c1e0237330d70a338e09232c39e6454cdbf143ee93cb745aff`.

## Installed delivery and actual normal-play result

With all editor/game processes closed, the final DLL and matching PDB were
installed into `unreal/Plugins/RaftSim/Binaries/Win64`. Original files were
copied and hash-verified first; recoverable backup:
`tmp/render-values-installed-backup-v1-20260917`. Installed gameplay DLL SHA256:
`8c0113680ce23823cda67bdb05762f6d87128426e52771efc89709628435dee6`.
Installation record: `tmp/render-values-install-v1-20260917.json`; its initial
launch-verification field is false because it predates the following capture.

The installed build was then launched normally on
`/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`, scenario
`south_fork_full_descent`, station 8330, 1280x720 D3D12. **No candidate module
override, paired timing probe or parallel-path opt-in** was used. Project and
WaterDetail DLLs, map assets and standalone game executable were not replaced.
This installs the gameplay module for editor/uncooked play, not a packaged build.

The 300-frame capture completed with exit 0. Unchanged inclusive sample window
60-240 has 181 rows:

- Elapsed-frame average: **30.285471 FPS**; mean **33.019134 ms**.
- p95: **41.4455 ms**, exceeding **33.333333 ms**: **FAIL**.
- Game thread 32.863251 ms; GPU 11.087512 ms.
- RenderPacket 0.497181 ms; crest selection 3.232256 ms overall,
  7.312979 ms on its 80 active frames; SetMesh 9.466768 ms.

These scopes overlap/nest; do not sum them. This short ordinary run does not
isolate the whole-frame difference from the previous 28.057157 FPS capture.
Only the paired conversion timings establish this change's local speedup.

CSV `unreal/Saved/Profiling/CSV/south-fork-render-values-installed-v1-20260917.csv`,
SHA256 `1901b44447f9c2ee90f5e99cb7861c5e42d3b194910cdf85707234dd75dc8670`.
Audit `tmp/south-fork-render-values-installed-v2-20260917-audit.json`, SHA256
`fde327b6318b7efc4095d3b128fddfaef1fcfba7b770a78e21919217d50c2609`.

## Actual images: visible defects remain

The installed default runtime and backed-up old runtime each completed a separate
24-image 1280x720 startup sequence. Installed frames 000/011/023 and old frames
000/023 were visually inspected. Water is present from the first image; later
images show moving crest/foam structure. Both builds show the same conspicuous
angular green water edge/exposed bed at startup and broad sheet-like white foam.
The defect therefore predates this installation, but remains a visual failure.
The separate runs are not exact-time or pixel-identical motion comparisons, and
no real-video fidelity, crew-quality or camera-water-contact gate is accepted.

Images: `unreal/Saved/Screenshots/south-fork-render-values-startup-v1-20260917_000.png`
through `_023.png`, with the corresponding `old-startup` sequence retained.
Process/image-hash witnesses under `unreal/Saved/RaftSimValidation/`:

- `south-fork-render-values-startup-v1-20260917-process.json`, SHA256
  `89b7cb9134ac9d6741e96d7aa6c56f0ab98d5afcbe4cb67e966428ba00d7a182`.
- `south-fork-render-values-old-startup-v1-20260917-process.json`, SHA256
  `770e3b8685f0f18d6d597ef9d0d8573457e2530705c92d079f809701f5d3fa7e`.

All four capture sessions are terminal and resumed the explicitly identified
hydraulic process through retained handles. No editor/worker was restarted.

## Hydraulic continuation and next gates

Same cook PID 36872 remains live. The 2,600-second/local16,000 snapshot passes
state conservation and all 86,720 exactly dry exterior-bank cells. Maximum
depth 4.185816 m, speed 6.385897 m/s, volume 2,956,896.141752 m3, maximum step
conservation residual 1.647021e-8 m3. Outflow 92.453161 versus inflow
45.306955 m3/s: **NOT settled or promoted**. The 2,500 and 2,550 snapshots also passed
both audits; neither was accepted as settled.

- `tmp/control-ablation-2600s-state-v1-20260917.json`, SHA256
  `6278d9822733c0cde285da43677afcbeb0569fc8038920ce68704b14c10a2209`.
- `tmp/control-ablation-2600s-banks-v1-20260917.json`, SHA256
  `fdfdee48b7e9222880774fdfa8e7f6f2ea13a36e1322e90592449f18033aa425`.

Before commit, 2,650/local17,000 completed and passed both audits too. Maximum
depth 4.193144 m, speed 6.408453 m/s, volume 2,954,478.917858 m3; outflow
93.189388 versus45.306955 inflow m3/s: still NOT settled. Next2,700/local18,000
requires both audits after its completion marker; preserve the live cook.
State report `tmp/control-ablation-2650s-state-v1-20260917.json`, SHA256
`54bdaefe0a59213b99fd3241d64c6d382a5af4417b23adfedd1088c5d0a3dad8`;
bank report `tmp/control-ablation-2650s-banks-v1-20260917.json`, SHA256
`23a29d73ad3a1b5219109c9f05a2e12884b72ecf84814d60521830cbfd4a0fd4`.

Prioritize the observed startup water geometry/foam and expensive current-profile
selection, without freezing water or lowering detail; complete physical front/
energy/bed coupling and source-consistent terrain integration. Native prescribed
position regression is now closed in [its separate report](sm5-prescribed-normal-recovery.md).
South Fork visual/physical acceptance, sustained p95, Colorado then Pacuare then
Futaleufu, Chilko/Zambezi/all-scene review, crew, normalization and release remain
open. Troublemaker remains only a rapid within South Fork, not a menu scenario.
