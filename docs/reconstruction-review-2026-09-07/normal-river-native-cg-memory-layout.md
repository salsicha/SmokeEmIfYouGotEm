# Native pressure profile and exact slot-major memory layout

September14,2026,08:07UTC. Measured sparse actions dominate the current native
GPU cost. A storage-only layout change cuts sampled South Fork solve time from
123.915/128.062ms to52.495/52.501ms per pole, with all six solutions and diagnostics
BIT-EXACT to the independently audited original CSR run. Still FAR OVER budget;
no gameplay/native-geometry/history/scene promotion.

## Profile before choosing the change

Added explicit `-RaftSimReconstructedCGPhaseTiming` instrumentation to the isolated
`ReconstructedCGGPU` test. Each of325 scheduled phases has begin/end GPU queries;
the report retains counts, total and maximum intervals for each phase. Intervals
include necessary dispatch/barrier behavior and query instrumentation, not only
arithmetic instructions. This is a shared-load diagnostic, not warmed/isolated
production timing. The cook and both original CPU histories were not paused.

Full32768-unknown South Fork, both original actual RHS poles:

| Timed work | CSR larger/smaller(ms) | Slot-major larger/smaller(ms) |
| --- | --- | --- |
|41 preconditioner applications, phase3 |64.779 /63.847 |20.569 /20.569 |
|40 original matrix applications, phase6 |49.259 /48.461 |18.565 /18.535 |
|Entire clear/initialize/40-CG bracket |128.062 /123.915 |52.501 /52.495 |

The two sparse-action phases account for89.05%/90.63% of the original measured
brackets. Final reductions were not the dominant cost. The before/after runs
are separate single shared-load samples; repeated interleaved comparisons and
complete production cost are still required. The remaining~52.5ms per pole is
not compatible with the production component budget or a30FPS playable claim.

## Exactly what changed

New opt-in `-RaftSimReconstructedCGSlotMajor` and matching shader permutation.
Original CSR row offsets/counts stay unchanged. Coefficient slot j of row i is
stored at j*N+i, allowing adjacent GPU threads to read adjacent coefficient and
column data. Within every row, the original column order and FP64 coefficient
bits are preserved. Each row reads only its original number of entries; padded
storage is NEVER read as an added physical term. Original CSR remains available
as the control. The native CPU reference continues to apply the original CSR.

South Fork has maximum row width14:458,752 slots store all328,032 original
entries per pole. Both original A and scaled S coefficients, and all column
indices, are copied exactly. The extra slots trade bounded storage for coalesced
access; they do not reduce geometry, coefficients, precision or fidelity. The
test explicitly rejects layouts exceeding64M slots rather than truncating them.
This test allocation guard is not a new physical acceptance criterion.

The shader changes only entry addressing in phases3 and6. It keeps FP64
multiply/add order, all40 iterations, exact-zero-only exits, power-of-two range
normalization and original residual gates. No source, bed, state, native geometry
assembly, boundary, adapter, gameplay or live Python dependency was edited.

## Verification and provenance

- Build17451 terminal exit0,17.53s; profiled CSR engine66984 terminal exit0.
  Both `ReconstructedCGGPU` and `ReconstructedPolynomialGPU` pass.
- Build41789 terminal exit0,16.78s; slot-major engine37633 terminal exit0.
  Both actual D3D12 GPU tests pass again. Selected RHI is RTX3060 Laptop GPU;
  the automation report's AMD metadata is not the rendering adapter.
- Every GPU solution bit, native CPU solution bit and diagnostic field for all
  six cases matches `south-fork-reconstructed-cg-native-parallel-v1-20260914.bin`.
  Comparison first verifies that binary's SHA against the PASSED independent
  original factored-operator audit. Timestamps are the only excluded fields.
  Both comparison commands exit0. Thus original true/depth-weighted residual
  checks transfer to the identical values, not to merely similar output.
- Original source fixture SHA remains
  `4e53b1bab29626585d3d017408d9043956fa61f5077cc55cd4087f1229a6feb4`.
- Profile output `tmp/south-fork-reconstructed-cg-phase-profile-native-v1-20260914.bin`, SHA256
  `f7df9ee8984fbe011be4fb8185f699bb2147a3e9f2f086ae9bce424884939091`.
- Profile report `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-phase-profile-v1-20260914/index.json`, SHA256
  `ad3daac11c27050af36329153b5b1c8f4825419fdc67d9b69adcbd9517aafb1e`.
- Slot-major output `tmp/south-fork-reconstructed-cg-slot-major-native-v1-20260914.bin`, SHA256
  `2d2b3e618ec3151352f5ffc11bdae7300a1876aa5065e38da42b70c6f7922b5a`.
- Slot-major report `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-slot-major-v1-20260914/index.json`, SHA256
  `519855f525b1a3d858b36634f4a611891c347f77a0cf044c783ec6589b1105bd`.
- Final shader SHA256 `cf1dbb959e6aae36c92e22c4f24619a7ca5e2ae788dea7d723481e124c7bca9e`;
  C++ test SHA256 `937ba205f2494813420d7d6b2150d9e6fef117be8863c7c70a17dce286fcaf5b`.
- No Python implementation changed; the most recent combined Python suite is
  the previous139-test/8.10s pass. Current verification is the two GPU regression
  runs plus complete bitwise/diagnostic comparisons, not a new Python-test claim.

## Live work and next action

BOTH complete7800s/local36000 cook audits pass. All5,382,400 cells finite and
all86,720 artificial-bank cells exactly dry,2276 shared directed faces. Volume
2,635,463.953519446m3, driver residual2.793968e-9m3. Outlet104.002367127m3/s
still exceeds inlet45.306954547m3/s: settling and runtime source promotion remain
unproved. Cook74818/PID41820 remains live; next COMPLETE7900/local38000 needs
BOTH audits. No restart/pause or source mutation.

MAIN59896 remains live toward9.066667139530182s and both moves. Last accepted
observation0.42362909694069173s, maxspeed21.91656m/s,18 rejected trials in that
interval, mass residual2.52243e-13m3. Diagnostic95666 remains a separate live
old-failure-time prefix. Both original dependency sets remain frozen.

NEXT: verify repeated/interleaved layout timing and optimize the remaining
measured sparse actions/dispatch cost while preserving original inputs, range,
precision and independent residual gates. Broader native range/failure cases,
native geometry/rates, physical history and playable integration remain open.
Latest actual gameplay18.899245FPS/p9570.33ms still fails the30FPS target. No
new scene capture or production water promotion; full remaining-work scope stays
active, including other rivers/crew/regressions/release/final commit.
