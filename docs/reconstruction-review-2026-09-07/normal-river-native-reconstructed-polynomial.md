# Original reconstructed operator and bounded polynomial: native arithmetic

September 14, 2026, 07:38 UTC. Isolated native CPU and actual D3D12 SM6 GPU
arithmetic PASS on the original reconstructed matrix and actual nonlinear RHS.
This is NOT a full native solve, cost measurement, physical history or scene pass.

## What changed

`physics/scripts/export_reconstructed_polynomial_fixture.py` captures both
unchanged pressure solves for the fine solitary profile, variable-bed 2D case,
and FIRST original South Fork observation/boundary bracket. It exports the CSR
matrix A, symmetrically scaled matrix S, inverse diagonal roots, actual RHS,
original factored-operator action, degree-one preconditioned RHS, and arithmetic
error scales as binary FP64. It retains original source/dependency hashes and
checks that neither state nor bed changed. No manufactured A*x replaces the RHS.

`RaftSimReconstructedPolynomialTest.cpp` independently checks native CPU CSR
loops against the original factored Python action, then dispatches the isolated
`RaftSimReconstructedPolynomialTest.usf` kernel and reads actual GPU results.
FP64 values travel as uint2 bit patterns. The shader uses precise double
multiply/add and the reference polynomial ordering, with no cutoff or repair.

The preconditioner is the existing degree-one matrix-bounded candidate:
S=D^-1/2 A D^-1/2, omega=1/max(row sums(abs(S))),
P r=omega D^-1/2 (2I-omega S) D^-1/2 r.
This changes no physical damping, original operator, source or state. The kernel
is test-only and is not called by the production water solver or gameplay.

Every component is checked against 128*FP64 epsilon times its absolute-sum
arithmetic scale. This checks tiny rows separately; a global norm cannot hide
them. These roundoff checks do not replace or relax the original 2e-5 pressure
residual gate. No full GPU pressure residual was measured in this test.

## Evidence

- Fixture `tmp/south-fork-reconstructed-polynomial-native-v1-20260914.bin`, SHA256
  `4e53b1bab29626585d3d017408d9043956fa61f5077cc55cd4087f1229a6feb4`.
- Manifest with all source/module hashes:
  `tmp/south-fork-reconstructed-polynomial-native-v1-20260914.json`, SHA256
  `d81d0979f5f26c8382c6609aff7f17dd462758ad4b3530634c3e977af3b390a0`.
- UE5.8 Win64 Development Editor build session43004: exit0,23.44s.
- First engine launch77178: exit1, missing mandatory Platform.ush include;
  its v1 log is retained. Only that shader include was corrected.
- Actual retry53934: exit0, automation Success with zero warnings/errors.
  Report `unreal/Saved/RaftSimValidation/south-fork-reconstructed-polynomial-v2-20260914/index.json`, SHA256
  `623ecf1faebc0ac4290358b874dfac5ed7ec46336a648372e3c60dc7c10ef45b`.
  Automation metadata reports AMD Radeon(TM) Graphics, but the authoritative
  RHI log selects adapter0, NVIDIA GeForce RTX3060 Laptop GPU / D3D12 SM6
  (lines986/998 of the v2 log). This correction was verified during the later
  complete-CG audit. No other backend is qualified.
- Shader SHA256 `62204b15d44e6fbf5ea3066dbd56dc1c7614f6164076aca83eab6c4d9fff874a`;
  C++ test SHA256 `4f7895ce2ad623af6278c9a9a07f9a7722a0560aad602011551b231cae7102f9`.
- Combined fixture, polynomial, physical-reference, reconstruction and runtime/
  release-budget suite: **131 tests pass in8.49s**.

| Actual RHS source | Unknowns per pole | Stored entries per pole | Maximum component-scaled GPU action error, two poles | Preconditioner difference |
| --- | ---: | ---: | --- | --- |
| Fine solitary | 1536 | 4488 | 5.58762e-16 / 3.58614e-16 | 0 / 0 |
| Variable-bed 2D | 768 | 10752 | 2.73488e-16 / 3.60270e-16 | 0 / 0 |
| Original South Fork | 32768 | 328032 | 6.59164e-16 / 6.58657e-16 | 0 / 0 |

South Fork's smallest scaled coefficient is1.097874909973476e-44: FP32
subnormal, not zero. The exporter reports zero coefficients lost by a CPU FP32
cast for these particular matrices, but that does not establish correct GPU FP32
arithmetic. This FP64 test preserves the exported doubles instead. It does NOT
qualify the native finite-volume activation rates below FP32 range, native
reconstructed D/E assembly, geometry derivatives or boundary/wetting updates.

The0.1228514s automation duration includes CPU verification, uploads, readbacks
and synchronization across six cases; it is NOT GPU component cost or frame time.
No timestamp benchmark or complete40-iteration GPU CG was run. Earlier captured
CPU solve costs remain failures, and the production cost gate is unchanged.

## Live histories and next work

MAIN59896 remains the unchanged original-start full9.066667139530182s/two-move
request, not the old failure-time prefix. Last accepted observation during this
work:0.34912471835695796s, maximumspeed23.61431m/s, five rejected trials in that
interval, mass residual-8.98726e-14m3. Increasing speed/retries are retained, not
declared stable. Diagnostic95666 remains live separately. Neither dependency
set was edited, and no candidate preconditioner was installed in either run.

Cook74818/PID41820 is unchanged. BOTH complete7700s/local34000 audits pass:
5,382,400 finite cells,86,720 exactly dry artificial-bank cells,2276 shared
directed faces. Outlet104.855539 versus inlet45.306955m3/s remains unsettled.
Next COMPLETE7800s/local36000 requires BOTH audits.

Next: complete fixed40-iteration native CG parity/true-residual checks on the
same original operator and actual RHS, then measure complete cost. Keep it
isolated pending original-history, independent physical, wetting/boundary and
native assembly qualification. Outer wave/foam return coupling, contact and
playable captures still remain. Desktop30FPS remains the target; latest actual
18.899245FPS/p9570.33ms still fails. No scene acceptance or final commit.
