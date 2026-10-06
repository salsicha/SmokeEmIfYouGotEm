# SM5 cook recovery and packaged-source qualification

September 16, 2026. Progress, NOT package, gameplay, visual or 30 FPS acceptance.
The preceding commit-only turn reconfirmed clean Git state; it did not advance
the remaining goal. This turn resolves two actual shader compilation defects
and audits the next completed hydraulic states.

## Authoritative package failure

The original package job was left intact until it terminated. Session80881
returns UAT exit25; cook16144 exits3 after9,520.14s. The final worker completed
its actual task, reporting3,818.553s, before the cook reported36 SM5 shader
errors. The earlier lack-of-state-change warnings were not terminal failures.
No archived package was produced. Do not restart the same unmodified cook.

The AutomationTool moved the cook log on completion; its old Engine/Saved path
no longer exists. Retained log:
`C:/Users/salsi/AppData/Roaming/Unreal Engine/AutomationTool/Logs/C+Program+Files+Epic+Games+UE_5.8/Cook-2026.09.16-03.16.03.txt`.
SHA256`3b60853b5ed412185b5ffb2b0fc17c4f265f8d028ba640985ce98ee1bf8cba63`.

Errors include acceleration barriers reached through compiler-varying UAV
conditions, a variable-indexed vector l-value in prescribed-normal rounding,
large-loop/unroll failures in acceleration preparation/pressure/transport, and
secondary compiler internal/SPIR-V failures. Installed engine source confirms
`CFLAG_ForceDXC` raises the shader model; it is NOT used to evade SM5 support.
No target, permutation, numerical tolerance or iteration budget was removed.

## Verified corrections

Prescribed-normal correction keeps the original dominant-axis arithmetic and
rounding, but explicitly stores X or Y. The original saved preprocessed shader
reproduces FXC X3500; the corrected copy compiles with the same cs_5_0/O3 flags.
No original compiler dump is edited. First actual D3D12/SM6 GPU run18176 exits0,
and its existing65 independently computed coordinate cases remain bit-exact.

Acceleration now broadcasts its immutable dispatch error/inactive decisions
through lane0 and group-shared storage before early returns. Every lane reaches
the initial barrier, and subsequent barrier control is compiler-proven uniform.
The equations, reduction arithmetic/order and40-iteration budget are unchanged.
No device-wide spinlock or cross-workgroup shared state is introduced.

All eleven retained barrier-failing SM5 permutations compile after applying the
same correction to private copies of their original preprocessed inputs:
0,2,4,6,8,12,14,16,18,26,28. This is focused FXC compilation, NOT a repeated
full-engine cook or actual SM5 GPU execution. FXC still reports finite-value
optimization and register-pressure warnings; these are not waived as runtime
qualification. Report`tmp/sm5-acceleration-compiler-v1-20260916/report.json`, SHA256
`0d5edbe83fa441ded15e9a35eac15c5fbf751a1547360e64fbc5cdb2635239a6`.

Actual-engine session36172 exits0: both acceleration and prescribed-normal
tests PASS, zero test warnings/failures/not-run,3.544037580s. The acceleration
suite covers single-group, distributed, fused and indirect paths; periodic,
dry/tiny-depth, invalid inputs, both individual inactive poles and full-domain
cases up to512x512. Existing indirect/direct solution/residual/diagnostic exact
comparisons and independent numerical gates pass without changes. This executes
the production shader in D3D12/SM6, not a CPU imitation or SM5 runtime claim.
Report`tmp/sm5-barrier-fix-native-v1-20260916/index.json`, SHA256
`025df0c99ddb542d234c1c702dfc01661e107e7d8f2e6e15e5ad05d415b553bc`.
Existing optional Toolset startup errors remain separate from these test results;
this is not a clean release run or a performance measurement.

Current shader SHA256:

- Prescribed-normal: `33d6f26649f56d6ee06e2594c715d924d54d0f31669ebfb2f88fc0e82b729f4e`.
- Acceleration: `4b53cb69036bbf197467f19666cbdc8215fc47be528d5ff9e1b270e708813a58`.

## Remaining compiler work — active isolated probe

Preparation/pressure/transport unroll/internal errors are NOT fixed. The
compiler-suggested explicit two-iteration annotation is being tested only in
`tmp/acceleration-prepare-sm5-unroll-v1-20260916.usf`; it is NOT in production.
Session13666 / FXC PID15160, start2026-09-16 03:27:31 local, was independently
confirmed live with increasing CPU time. Poll the same job; preserve its output
and original input. Do not launch another long full cook before addressing the
remaining failures. A successful isolated probe would still require production
integration, actual GPU regression and full cook/packaged evidence.

## Reproducible packaged acceptance runner

`physics/scripts/verify_packaged_ground_sources.py` ties a fresh process/report
to the expected game-executable SHA and the versioned retention receipt. It
requires the complete unchanged before/after directed-triangle identities,
rejects missing/duplicate/additional assets, checks each CPU-access and
non-editor flag, and independently compares all native identity fields. An
exit0 with no report, a top-level pass over a subset, or an editor report fails.
It checks the self-contained runtime bundle both before and after execution,
checks unchanged executable/receipt bytes, and never updates historical evidence.
Its output keeps gameplay/physical/visual/performance acceptance false.

Actual receipt derivation matches the existing expected manifest exactly:
444 assets /9,211,652 directed triangles.96 related Python tests PASS in2.80s,
including process-orchestration failure controls, retention and runtime bundle
tests. The first expanded command named a nonexistent test file and ran no
tests; only the corrected actual selection is counted. Fake-executable unit
tests are explicitly not native package evidence. The runner has NOT yet run
against a completed package, and the retention receipt remains unchanged.

After shader recovery, require the archive executable SHA
`18d9e4b24bc845192a26ca5f50212111ff6d4d2a8cf29d1bf23fd6576ef785d1`
(or a subsequently documented verified build), then run the audit with the
retention receipt, `physics/data/runtime_bundles/south_fork_saved_scene_v1`,
and a fresh output directory. Only then proceed to packaged play/contact and
uncontended performance. The current Game embeds solver archive2ce80e6f...;
editor DLLs have not yet been relinked to that newer solver.

## Hydraulic continuation

The SAME corrected-domain job18716/session69416 continues unchanged. Completed
local6000/7000, absolute1500/1550s, pass all5,369,600 cell checks and all86,720
exactly dry artificial-bank face checks. At1550s: max depth4.517990022m,
max speed7.219694005m/s, volume3,007,919.921847134m3, maximum per-step conservation
residual1.378528425e-8m3. Outflow86.619794112 versus inflow45.306954547m3/s
rejects settling. No runtime-field or geometry promotion follows from these passes.

Reports `tmp/south-fork-context3-{1500,1550}-{snapshot,banks}-v1-20260916.json`:

| Evidence | SHA256 |
| --- | --- |
|1500 state|`770a62cdd823edbff358ce0b07eb642aece049ca6e4ec28fa02a9b4ca6e66377`|
|1500 banks|`b17ef0a64dbdbc9d1bb39610fe4e830aeffc0db5ef7a1a76c2cdc1fcddaf26fe`|
|1550 state|`5fbb1e8dd1a5201ba9492604aaa1d4b7c4f55f2cca453d418750a2f5636a398e`|
|1550 banks|`e49c22fb3afec66d9469185f6755608e7a0a5e8ea46ad91b2171253050199525`|

NEXT complete local8000/absolute1600s needs BOTH audits. Last uncontended normal
play remains17.819710FPS/p9581.6343ms, failing30FPS/33.333333ms. Broad froth,
source-supported flanks, sustained playable integration, physical regressions,
Colorado -> Pacuare -> Futaleufu, other-scene water, crew and release stay OPEN.
Troublemaker is a rapid within South Fork, never its own menu scenario.
