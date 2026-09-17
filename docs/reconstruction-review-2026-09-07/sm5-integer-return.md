# SM5 encoded-return correction

2026-09-17 UTC. A real arithmetic defect is corrected; this is not river,
nonlinear-solver, rendering, performance or release acceptance.

## Cause and correction

The original SM5 engine suite failed exact addition despite bit-exact transported
inputs. A standalone FXC probe compiling the actual production helpers reproduces
734 compact-add and782 independent wide-accumulator mismatches in64,078 cases.
Both negative zero and nonzero subnormal results become positive zero. The
generated DXBC contains literal-zero selections where the source returns
`asfloat(sign|rounded)`; this loss happens during compilation, not buffer upload.
Compiling with `/Gis` still produces the same734/782 GPU failures.

The helpers now return encoded `uint` bits internally, then convert once in
their existing float-returning public wrappers. Integer rounding, signs,
nonfinite-input policy, physical state storage and caller interfaces are unchanged.
This applies to compact addition, wide accumulator rounding (Euler/RK2), product,
division and power-of-two scaling. No depth floor, flush-to-zero policy, cutoff,
epsilon, relaxed comparison or physical limit was introduced. Baseline artifacts
are retained locally; no engine compiler settings were changed.

## Actual SM5 execution

`physics/tests/portable_float_gpu_control.cpp` executes DXBC with D3D11 hardware
or WARP, loads the existing exact-rational fixture bytes without float conversion,
and reads every result back. Its companion HLSL includes the actual production
helper rather than copied arithmetic. For addition it independently checks the
original wide Euler accumulator as well as compact addition. An output operation
tag rejects a shader compiled for the wrong fixture. A deliberate division-shader/
addition-fixture mismatch exits1, with all64,078 operation tags rejected.

| Operation | Cases | Before correction: hardware errors | Corrected hardware / WARP errors |
| --- | ---: | ---: | ---: |
| Euler | 4,133 | Not separately replayed | 0 / 0 |
| RK2 | 8,229 | Not separately replayed | 0 / 0 |
| State admissibility | 8,250 | 0 (unchanged) | 0 / 0 |
| Division | 17,159 | 1,471 | 0 / 0 |
| Square root | 16,672 | 0 (unchanged) | 0 / 0 |
| Power scaling | 16,672 | 3,009 | 0 / 0 |
| Product | 34,875 | 3,065 | 0 / 0 |
| Addition | 64,078 | 734 compact;782 wide | 0 / 0, both implementations |

Total170,068 cases per backend. All transported input bits and operation tags
also match. The same compact-add source compiled as C++ passes all64,078 cases;
52 existing Python oracle/resource checks pass. These are scalar qualifications,
not full-step energy, long-running wetting, SM6 parity or engine qualification.
An existing FXC loop-variable-shadow warning remains visible in compile logs.

Retained evidence:

- `tmp/sm5-integer-return-scalar-v1-20260917.json` records source, fixture and
  compiled-shader hashes plus every hardware/WARP result. SHA256
  `e0bea3dd0534629d4b6b30c4572f62ba4b3fb94372f1abf7ffa1d1028f34ffab`.
- `tmp/sm5-add-baseline-v1-20260917-gpu.log` and
  `tmp/sm5-add-strict-v1-20260917-gpu.log` retain original and `/Gis` failures.
- `tmp/sm5-scalar-before-opN-v1-20260917*` retains the division/product/scaling
  failures; that intermediate build already includes the addition/affine fix.
- `tmp/sm5-scalar-fixed-opN-v1-20260917*` retains compile logs, DXBC, assembly,
  hardware and WARP outputs for each scalar operation.

Reproduce from a Windows x64 developer command prompt with the Windows SDK:

```text
cl /EHsc /std:c++17 /O2 physics/tests/portable_float_gpu_control.cpp /Fo:tmp/float-control.obj /Fe:tmp/float-control.exe d3d11.lib
fxc /T cs_5_0 /E MainCS /O3 /Gec /Zpr /D RAFTSIM_TEST_OPERATION=9 /Fo tmp/add.cso /Fc tmp/add.asm physics/tests/portable_float_gpu_control.hlsl
tmp/float-control.exe tmp/add.cso tmp/portable-add-fixture-v1-20260916.bin
tmp/float-control.exe tmp/add.cso tmp/portable-add-fixture-v1-20260916.bin warp
```

Use the recorded fixture/operation mapping for the other cases. Addition fixtures
can also be regenerated with `export_represented_float_fixtures.py --add` using a
fresh `--output` path; do not overwrite retained fixtures or change their oracle.

## Engine replay is live, not passed

Session9319 / PID9976, start2026-09-17T00:47:10.9340611Z, is replaying29 applicable
original SM5 failures with their original fixtures: arithmetic,16 evolution-owner
clock/slot/run-ahead combinations, total-depth stepping, temporal boundaries,
breaking front and prescribed-normal reconstruction. No result is claimed yet;
the engine is compiling dependent shaders. Preserve this job and its frozen
shader inputs until terminal. No installed DLLs or assets were replaced.

`tmp/sm5-integer-return-native-v1-20260917-process.json` records exact arguments,
selected tests and shader-input hashes; SHA256
`1f119d63cec1928ec83d3f7d6598ff505fdaaccf98dd046470e4ad5cd403a34a`.
Log and report use the same prefix. ReconstructedCGGPU and
ReconstructedPolynomialGPU require SM6/FP64 in the current test implementation;
their original SM5 failures remain open, not waived or counted as passes.
The original51 clean passes and one warned pass were not silently reclassified.

The additional encoding defect in `RaftSimDyadicRound` in
`RaftSimExactHydrostatic.ush` is now reproduced independently: a dyadic-addition
probe fails781 of the same64,078 exact-add cases, with zero transported-input
errors and zero failures in the already-corrected wide control. The finite dyadic
rounder has no signed-zero/nonfinite-input policy, so those scalar-fixture cases
are handled explicitly outside it; the expected fixture bytes are unchanged.
This is a rounder check, not the full reconstructed-face or pressure oracle.

A mechanically generated local candidate merges its encoded integer returns
before the bitcast and passes all64,078 cases on hardware and WARP. Candidate
`tmp/sm5-dyadic-return-candidate-v1-20260917.ush`, SHA256
`521b50bac053ebebe1c6fe52ee39b96ede91fd76c85d5a7181f62d6211e987e0`.
Baseline probe/compile/assembly/GPU evidence uses
`tmp/sm5-dyadic-return-probe-v1-20260917*`; candidate evidence uses
`tmp/sm5-dyadic-return-candidate-v1-20260917*`. This candidate is NOT applied to
production while the engine replay is live. Next, retain that terminal result,
integrate the dyadic return correction, then run exact-face and full-step gates.
Do not assume the scalar repair resolves every reconstructed-pressure failure.

The hand-written `physics/tests/*.hlsl` regression source is explicitly normal
Git text. The existing LFS rule for captured HLSL dumps elsewhere is unchanged.

## Ordinary play and hydraulic continuation

The installed ordinary-map detail replay58473 is terminal0/PASS: eight post-ready
handoffs,11,945 fresh frames and471.816691 detail seconds with unchanged gates.
The final image still fails visual acceptance. See
[the installed startup and continuity record](checkpoint-terrain-startup.md).
Last ordinary performance remains26.784840FPS/p9543.5724ms, FAIL30; no new FPS claim.

The same hydraulic cook11316 resumed and completed absolute1400s/local16000.
State and all86,720 exact-dry artificial-bank-face checks PASS. Maximum depth
4.545990m, speed6.913665m/s, volume3,013,803.325m3, maximum per-step conservation
residual1.707900e-8m3. Outflow82.238582 versus inflow45.306955m3/s: **not settled**,
not promoted into the ordinary map. Next1450s/local17000 requires both audits.

- State report `tmp/control-ablation-1400s-state-v1-20260917.json`, SHA256
  `64430b52e0e4d279696ed719f49d14b2ae6937315799c6696f6a70fb74086ec3`.
- Bank report `tmp/control-ablation-1400s-banks-v1-20260917.json`, SHA256
  `f1bf0184dfcdf3c994a001aeaad96c6731decaa70e86952d28224954d2a71051`.

Continue the full South Fork reconstruction and coupled physical/visible water,
30FPS, distant in-run reset, source closure, normalization, Colorado -> Pacuare
-> Futaleufu, Chilko/Zambezi/all-scene reviews, crew and release queue. Troublemaker
remains a rapid inside South Fork, never a menu scenario. Full goal remains open.
