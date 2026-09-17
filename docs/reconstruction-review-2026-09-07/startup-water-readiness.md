# First-frame water readiness — 2026-09-17 UTC

## Implemented and installed; not scene acceptance

The ordinary South Fork first capture now contains water. The unchanged installed
baseline `south-fork-startup-water-normal-baseline-v1-20260916` has neither water
nor terrain in image 000. The fixed installed replay
`south-fork-startup-water-installed-v3-20260916` has water in image 000, with no
module override, paired-preview, full-hull or render-audit flag. Both complete
all 24 actual 1280x720 frames with no warmup discard. Terrain is still missing
initially and appears later in ordinary gameplay; that pre-existing startup
problem is not fixed. Crew colors also arrive late. Angular green crests,
broad smooth froth and unfinished terrain/crew remain visibly unacceptable.

The water component now prepares its own incomplete SingleLayerWater material
before its first mesh publication in rendering editor game worlds. It uses the
engine's scoped synchronous material cache and completion APIs. No global shader
flush, hard-coded shader type list, capture delay, hydraulic clock change,
resolution reduction or quality change is introduced. Complete materials skip
the work. Non-rendering/non-game worlds and cooked builds do not compile shaders
through this editor-only path. Cooked startup readiness remains to be verified.

An initial causal experiment prepared just NoLightMap BasePass VS/PS. Those
shaders were present from render frame 4, but image 000 remained dry. Preparing
the complete material, including its depth/velocity permutations, produced
visible first-frame water. This supersedes the earlier inference that BasePass
availability alone explained the missing water. Material preparation took
0.136030 s in opt-in v2, 0.149216 s in default v3, and 0.138055 s in the installed
replay. These are observed warm-cache startup costs, not cold-cache guarantees
or recurring frame costs. The first-frame visual result was inspected directly.

## Build, regression and deployment evidence

- Actual linked unity unit 3 compiled; isolated gameplay DLL linked successfully.
  Unit 5 retains the committed checkpoint-before-water ordering correction.
  All five linked gameplay objects have no newer local source dependencies
  (57/76/94/78/56 local source entries respectively).
- Five native tests PASS: StartupWaterAfterSessionRestore,
  ReconstructedSessionContracts, RunProgressDistinctFromRapidHydraulics,
  CoordinateFrameProgress and ShorelineCompactUpload. No warned passes/failures.
  `tmp/startup-water-shader-native-v3-20260916/index.json`, SHA256
  `2badd4e3e13d8b05c894b612ab4a3f02754f7e2e5c8b197fea40b502da3b73c4`.
- Four new source-contract checks plus existing preview/retention/session checks:
  **84 PASS**. Source checks constrain scope; actual images establish rendering.
- Default v3 paired-preview replay completed 24 frames, SHA256 of process report
  `dbb579a0ac5a890e546c4a726227f2b685f29217210698e7c354015b2a62978c`.
- Ordinary installed-project/candidate-gameplay replay also completed 24 frames
  without preview/full-hull/audit flags, before installation.
- With all editor processes stopped, the former installed DLL/PDB were copied to
  `tmp/startup-water-installed-backup-v3-20260916/` before replacement. Former DLL
  SHA256 `14e578ba824b73ce9cb90c733eb4cfba2a30b8fdd04261034bbe15448f54d591`;
  installed v3 SHA256
  `947f5a53a9927872c2ce72acf98c93ce2c04c14d1fe3e650da0c56f47201d942`.
  Project, editor, physics and detail modules and map assets were not replaced.
- Installed replay exits 0 and records the new startup preparation message with
  no override bootstrap. Process report SHA256
  `c0f1e9eb698598a290112de81ae615134f96537cb6c9b65db84da01371e6d3ba`.
  Attempts to collect a live module-list witness missed the short-lived process;
  no fresh process-module-list witness is claimed.
- All scoped replay runners resumed the same hydraulic cook successfully;
  subsequent CPU progress was verified. Generated evidence/binaries stay ignored.

## Ordinary installed performance still fails 30 FPS

`south-fork-water-startup-installed-perf-v3-20260916` uses D3D12, actual1280x720,
the ordinary South Fork map and installed modules, no review/preview/audit flags.
All300 CSV frames are present. The unchanged inclusive60–240 window (181 rows)
measures **26.784840 FPS**, mean37.334551 ms, p95**43.5724 ms**: FAIL against
33.333333 ms. No optimization improvement is claimed from this unpaired run.

Inclusive mean scopes: game37.19 ms, GPU12.81 ms, water tick22.96 ms,
CartesianPublish12.49 ms, SetMesh11.27 ms, crest update8.08 ms, solver6.07 ms.
These overlap and must not be added. Startup correction does not close the
sustained/packaged performance gate or the outstanding SM5 failures.

CSV SHA256 `9340284e83279dc6feaf9e3ed61a17d86c42aaffa5e860b257d8491729f0b6b9`;
audit `tmp/south-fork-water-startup-installed-perf-v3-20260916-audit.json`, SHA256
`dc0ec0f04d29ab7ac16931fa123c5ba2e42126d2f34fbd52e238db4a5abaf07d`.

## Hydraulic continuation: safe checkpoints, still not settled

The same 841-tile/5,382,400-cell solve reaches1250 and1300 seconds. Both state
audits and all86,720 artificial-bank-face checks pass; artificial banks remain
exactly dry. Inflow45.306955 m3/s remains below outflow76.789859 and78.768740 m3/s.
Volume falls to3,018,950.431 and3,017,327.052 m3 respectively. At1300s maximum
depth4.559993 m, speed6.914053 m/s, maximum step conservation residual1.707900e-8 m3.
Neither checkpoint is settled or promoted into the normal map.

Reports under `tmp/`, SHA256:

- `control-ablation-1250s-state-v1-20260916.json`:
  `d490aa0f8fa3a11913e52b0a3ca53fb8a86de5f10b593dae108d30766db1372b`.
- `control-ablation-1250s-banks-v1-20260916.json`:
  `2c994509c8a5cfac0c786323b624dfe388755dbcc94eb40f03fa3afbe22107e7`.
- `control-ablation-1300s-state-v1-20260916.json`:
  `95edcf67ae18210fa8919eccf1179e7aa546a4d3fe130e1ca249a4d44e75b060`.
- `control-ablation-1300s-banks-v1-20260916.json`:
  `ab064da08e6372fcea21bcc7af5185db44af334ecdf825f1b35b2de90f50030e`.

Cook11316 remains live with original start identity. Next checkpoint1350s /
local15000 requires both audits. Next implementation work: ordinary terrain
startup readiness, consistent terrain/collision/hydraulics, coupled nonlinear
water and crest/froth realism,30 FPS and the remaining complete project queue.
Troublemaker remains a rapid inside South Fork, never a menu scenario.
