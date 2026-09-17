# Shoreline validation and isolated full-face SM5 evidence

2026-09-17 UTC. This is measured partial progress, not visual, physical,
geographic, normal-installation, sustained-performance or release acceptance.
Troublemaker remains a rapid within South Fork, never a menu scenario.

## Committed shoreline optimization

Commit `6a0312304` fuses vertex validation with the exact shoreline-cache reuse
predicate, partitioned into independent 1,024-node batches. It preserves all
finite/depth/wet checks and validates every node even after an earlier cache
mismatch. No output/cache mutation occurs before complete successful validation.
No geometry resolution, update frequency, physical model or gate was weakened.
The original two-pass control remains available with
`-RaftSimSeparateShorelineValidation`; serial fusion remains available with
`-RaftSimSerialShorelineValidation`.

Final isolated gameplay DLL compiled/linked successfully:
`tmp/shoreline-validation-gameplay-v4-20260917/UnrealEditor-RaftSimRaft.dll`,
SHA256 `54699d36b973ae63a5ed5613db68f5d374a402aec850b9afbdbfd6896d3cd5c2`.
Matching project module is the existing checkpoint-play-v2 candidate,
SHA256 `204f0a737ee55ba3905b57c47c29fa5aa270f82b7c0660e25de4df878fd1f7bd`.
These modules are explicitly loaded by the isolated bootstrap, not installed.

Final defaults passed all eight native D3D12 tests: ShorelineInputValidation,
CartesianShorelineGeometry, ShorelineExactCache, ShorelineMovingBankCache,
ShorelineCrestTargetCache, ShorelineFineCrest, ShorelineOppositeDryFan and
ShorelineCompactUpload. Zero warned passes, failures, in-process or not-run.
Session97556 / PID11060 terminated0. Native report
`tmp/shoreline-validation-native-rhi-v4-20260917/index.json`, SHA256
`190cf56df5d675bb659dadba94384670477b0c9cd9c702db3d41ac5f668e0da7`.
An earlier NullRHI experiment failed the rendering-proxy check; it is retained,
not substituted for this actual rendering-backed pass.

The final versioned paired audit compared 64 changing actual inputs, frames
122–185, totaling 3,240,000 vertex visits. Validation and cache decisions were
identical. Both orders won, all 64 individual candidate calls were faster:

| Call order | Pairs | Reference mean | Parallel fused mean |
| --- | ---: | ---: | ---: |
| Reference first | 32 | 1.959594 ms | 0.360869 ms |
| Candidate first | 32 | 1.724622 ms | 0.440088 ms |
| Combined | 64 | 1.842108 ms | 0.400478 ms |

All final-audit calls reused topology; separate native tests cover rebuilds,
moving/dry/rewet inputs and late invalid data across five batches. This comparison
proves the measured predicate optimization, not whole-frame or visual acceptance.
The earlier v3 pair also passed, including one non-reuse call.

Capture `tmp/shoreline-validation-pair-v4-20260917.json`, SHA256
`99eb4ac87e2fa972cc3f518d92ba6b07f35871f55b4500628479bd084c5c327b`.
Strict analysis `tmp/shoreline-validation-pair-v4-20260917-audit.json`, SHA256
`667938d8aae7980f6be354963de329a6ba03e786a84107e7d0984711ac652fa3`.
Session43078 terminated0 and resumed all four precisely owned background jobs.

## Ordinary frame measurement still FAILS 30 FPS

Separate non-audit, 300-frame ordinary South Fork run at 1280x720 D3D12,
Development/WindowsEditor, with the same candidate modules. No pair-timing or
render-replay overhead. Unchanged inclusive sample window60–240:181 samples.

- Elapsed-frame FPS: **27.068531**, mean36.943268 ms.
- p95 frame time: **43.391 ms**, FAIL versus33.333333 ms.
- Mean game thread36.717508 ms, GPU12.643852 ms.
- Mean water Tick22.013719 ms, CartesianPublish11.468988 ms,
  SetMesh10.223202 ms, crest Update8.318334 ms, Selection3.748164 ms,
  shoreline Topology1.015337 ms, StepWater6.494750 ms.

These scopes are nested and must not be added together. Historical installed
26.784840 FPS/p9543.5724 ms is not a same-input full-frame paired control;
do not claim a statistically established FPS improvement from these two runs.

Session93823 terminated0. Its scoped runner suspended/resumed only cook11316,
SM5editor9976 and workers31736/36256, each status0; CPU progress was rechecked.
CSV `unreal/Saved/Profiling/CSV/south-fork-shoreline-validation-perf-v4-20260917.csv`,
SHA256 `83518df7e22e994c4241d104b67dbfcdc4ed7eae0f5d1f77c315e3ddd8f896a2`.
Analysis `tmp/south-fork-shoreline-validation-perf-v4-20260917-audit.json`, SHA256
`5d27a25c98ae4936c94a7668d0c01860b86451c24954d3309127393e987d763b`.
Runner `unreal/Saved/RaftSimValidation/south-fork-shoreline-validation-perf-v4-20260917-process.json`,
SHA256 `f03b4bedf1890912e4ba560c17fbff5fe95fda925c557012917b9b65a2d09081`.

## Full hydraulic-face arithmetic, independently executed on SM5

Extended `physics/tests/portable_float_gpu_control.cpp` and its HLSL entry point
to read the unchanged 96-byte face records: four float4 inputs and eight exact
expected words. Every result word is compared bitwise, including both wet-side
Booleans and reserved zeros. A separate output vector checks transported input,
compiled operation, dispatch index and format tag. Scalar format is unchanged.
All shaders use FXC cs_5_0, MainCS, /O3 /Gec /Zpr; no floating tolerance or oracle
change. Both physical hardware D3D11 and software WARP actually execute bytecode.

| Shader/fixture | Cases per backend | Hardware | WARP |
| --- | ---: | --- | --- |
| Production exact face | 4,301 | FAIL:245 output words | FAIL:245 output words |
| Local dyadic integer-return exact face | 4,301 | PASS | PASS |
| Local candidate/scaled face | 4,317 | PASS | PASS |
| Existing corrected scalar addition and wide control | 64,078 | PASS | PASS |

No transported-input or dispatch-tag errors in these qualified runs. The exact
face baseline independently reproduces the subnormal-to-zero defect. The local
rounder correction changes return encoding, not polynomial arithmetic, wet-face
classification, float precision or geometry. It was already isolated in
`tmp/sm5-dyadic-return-candidate-v1-20260917.ush` (SHA256
`521b50bac053ebebe1c6fe52ee39b96ede91fd76c85d5a7181f62d6211e987e0`).
It remains **unapplied to production** until the existing engine job terminates.
The scaled path uses the already-corrected wide accumulator; its pass does not
establish unscaled nonlinear stability or full-step acceptance.

Exact fixture `tmp/south-fork-exact-hydrostatic-fixtures-v1-20260913.bin`, SHA256
`c6a03c6bfe2889facc72999af297d0e22521ef73b61a540c3836ef48d7283314`.
Scaled fixture `tmp/south-fork-scaled-polynomial-fixtures-v1-20260914.bin`, SHA256
`ac2d927e45fbb47bf1b25c1e5d24717b6e434f68548583cc04e4e803045c7c9f`.
The fixture exporters and independent rational expectations are unchanged.

Local compiled artifacts:

- `tmp/sm5-full-face-control-v1-20260917.exe`, SHA256
  `80b45351c147d3e9f8b455d1221b60cafa2632cbb9423fee6d92332c9f12eb75`.
- `tmp/sm5-full-face-baseline-v1-20260917.cso`, SHA256
  `c01fbd4330bbb6d3aaa0d8027ce6531b08ed1d3a1fd8676839f84a5269f1bd9e`.
- `tmp/sm5-full-face-candidate-v1-20260917.cso`, SHA256
  `07339b8bf095fbba3852a9957e615f20a250c06d2bc60ddbd145c6adb91061b2`.
- `tmp/sm5-full-face-scaled-v1-20260917.cso`, SHA256
  `6df3ab0d052b1da8233288d296cbac7bb1b755f39197786c0f3571a324b51761`.

Compile session27805 terminated0. Matching .asm/-compile.log files are retained.
FXC X3078/X4000 warnings and scaled X4714 register-pressure warning remain;
these are not warning-clean release results. Execution logs use baseline/
candidate backend-v1, scalar backend-v2, scaled backend-v3 prefixes. Earlier
scaled attempts had a nonexistent fixture filename and returned2, not passes.
An old addition binary lacked the required operation tag: all64,078 tag checks
correctly failed. A freshly compiled operation9 binary then passed both backends.

Fifteen opt-in actual-harness tests pass, covering both backends, scalar/face
padded dispatch, malformed header/count/truncation/trailing bytes and a wrong
final expected word, plus a wrong compiled operation with matching values.
With the shoreline/source-packing tests: **47 PASS**, no
skips. Generic hosts without explicitly configured Windows artifacts skip these
GPU checks; a skip is not acceptance. Set RAFTSIM_GPU_CONTROL_EXE,
RAFTSIM_GPU_CONTROL_ADD_SHADER and RAFTSIM_GPU_CONTROL_FACE_SHADER as documented
in `physics/tests/test_portable_float_gpu_control.py` to repeat them.

## Hydraulic continuation and outstanding work

Same cook40601/PID11316, unchanged inputs/executable, reached1700s/local22000.
State and all86,720 exactly dry artificial bank-face checks PASS at1600,1650 and
1700s. At1700s: depth max4.474720 m, speed max7.189311 m/s,
volume3,001,448.985201 m3, max step residual1.707900e-8 m3.
Outflow90.210308 versus inflow45.306955 m3/s: **NOT settled**, no promotion.

- `tmp/control-ablation-1600s-state-v1-20260917.json` SHA256
  `27216cf71bcd403f0d4a79c88cf745b8f47077be0a92ae4e7a516d0bf273d21b`;
  banks SHA256 `fcf3e9a74cc4bffcd8730bfbb4fda06c45210cbddcec4198fde73ec4dfa92e9e`.
- `tmp/control-ablation-1650s-state-v1-20260917.json` SHA256
  `a3f5bfa155ef8f87e4abe3433e3be7b35c974e2e12bdfe3ab237481dad9ac143`;
  banks SHA256 `f03ec34d9b0825b257d3f9b9349cf9176e1f83c896bd952ae73270f84a67cc25`.
- `tmp/control-ablation-1700s-state-v1-20260917.json` SHA256
  `58f23d4fb1887185b241903d76d5054674c985a6445683f5213e25cd7a2aa844`;
  banks SHA256 `99dab3446edf7420072f9a08cc008dd334c8f49e70f200225ea5d903313491b9`.

Original SM5 session9319/PID9976 and workers31736/36256 remain live; all63
witnessed shader hashes unchanged. Installed gameplay947f5a53... and
projectf11c1bc6... remain unchanged. No restart or terminal pass inferred.
Next1750/local23000 needs both hydraulic audits after its complete marker.

Next: terminal engine result, safe dyadic correction and full-step regression,
normal-installation/ordinary-play revalidation, coupled nonlinear physics and
convincing single-surface waves/froth, evidence-consistent terrain/boulders/
collision, sustained30FPS, source closure/normalization, Colorado then Pacuare
then Futaleufu, Chilko/Zambezi/all-scene water, crew and release checks. The full
goal remains open; arithmetic and predicate passes do not close scene work.
