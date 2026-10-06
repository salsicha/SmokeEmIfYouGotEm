# Original reconstructed pressure: complete native40-CG accuracy and cost

September14,2026,07:55UTC. Both native CPU and actual GPU complete the original
six static actual-RHS cases at40 iterations. Independent original factored-
operator and depth-weighted residual checks PASS without changing2e-5 gates.
The straightforward sparse FP64 GPU implementation is TOO SLOW for production.
Neither static solve accuracy nor completed tests accept evolved/playable water.

## Implementation and scope

Extended `RaftSimReconstructedPolynomialTest.cpp` with an isolated
`RaftSim.WaterDetail.ReconstructedCGGPU` test and
`RaftSimReconstructedCGTest.usf`. All matrices, coefficients, inverse roots,
actual RHS vectors and recurrences remain FP64, uploaded as uint2 bit patterns.
The original range-PCG recurrence retains power-of-two residual/search scaling,
physical-unit iterates, bounded40 iterations, and exact-zero-only termination.
There is no global small-initial-RHS exit, depth floor, coefficient dropping,
iteration increase or changed physical operator. The degree-one preconditioner
is the already-tested matrix-bounded polynomial, not water damping.

The initial implementation uses groupwise vector reductions with a serial final
reduction. A separate, opt-in shader permutation parallelizes the final reduction
over256 threads; the serial control remains. Changed summation order is checked
against the original operator, not assumed identical. Each variant allocates
all recurrence buffers once in an RDG graph, then schedules the complete solve;
there are no CPU readbacks inside CG. These are test-only paths.

`audit_reconstructed_native_cg.py` reads the actual retained native CPU/GPU
solutions. It re-captures the original nonlinear sources, verifies state/bed/
source metadata and complete exported operator/RHS payload hashes, then applies
the ORIGINAL factored operator to both native solutions. It checks original true
and depth-weighted residuals, and agreement with original-operator40-CG using
the bounded polynomial. Invalid/truncated/trailing/nonfinite output is rejected;
failed solve diagnostics are not repaired. Neither state nor live history
dependencies are modified.

## Independent accuracy evidence

Both serial and parallel variants complete40 iterations on both poles for every
case, with zero GPU diagnostic flags. Maximum native GPU solution difference
from original-operator CPU CG is4.51e-15 relative. The original polynomial
arithmetic regression also passes after both builds/runs.

Parallel variant, original factored operator applied to the actual GPU output:

| Actual nonlinear RHS | Unknowns per pole | Larger-pole true residual | Smaller-pole true residual |
| --- | ---: | ---: | ---: |
| Fine solitary profile | 1536 | 9.113767882e-7 | 1.233223461e-15 |
| Variable-bed2D | 768 | 5.371323324e-7 | 1.147948367e-14 |
| FIRST original South Fork observation/bracket | 32768 | 6.053105356e-10 | 2.766834939e-16 |

South Fork's larger-pole depth-weighted residual is1.233122758e-9. All true and
depth-weighted residuals remain below the unchanged2e-5 gate. No manufactured
A*x replaces any of these six nonlinear right-hand sides.

## Cost: not a production pass

Single shared-load GPU timestamp samples bracket clear/initialization/all40 CG
iterations. They are not warmed, isolated, repeated full-production benchmarks.
Geometry assembly, nonlinear RHS construction, two-pole combination, evolution,
contact and scene rendering are not included. Matrix/RHS fixtures are prebuilt.
The original cook/replay processes were not paused or restarted.

| Actual RHS | Serial final reductions, larger/smaller(ms) | Parallel final reductions, larger/smaller(ms) |
| --- | --- | --- |
| Fine solitary | 9.215 / 8.709 | 9.738 / 9.481 |
| Variable-bed2D | 9.709 / 9.712 | 10.673 / 10.676 |
| Original South Fork | 133.480 / 128.608 | 126.635 / 125.317 |

These observations are vastly above the unchanged production component budget;
do NOT promote this sparse FP64 implementation based on its accuracy pass.
The modest difference between shared-load runs is not a controlled performance
improvement claim. Parallelizing final reductions alone does not close the gap.
NEXT: per-phase GPU timing and an exact-input-preserving performance redesign,
with independent residual verification; do not guess which kernel dominates,
reduce resolution/geometry, discard small coefficients/rates or relax gates.

The authoritative RHI logs select adapter0, **NVIDIA RTX3060 Laptop GPU**, D3D12
SM6, integratedGPU=false. The automation report's AMD GPU metadata is misleading;
it is not the selected rendering adapter. The previous arithmetic document has
been corrected using its original RHI log as well. No other backend is qualified.

## Retained artifacts and process completion

- Original fixture unchanged:
  `tmp/south-fork-reconstructed-polynomial-native-v1-20260914.bin`, SHA256
  `4e53b1bab29626585d3d017408d9043956fa61f5077cc55cd4087f1229a6feb4`.
- Builds19155/98440 both terminal exit0,16.76/16.99s.
- Serial engine31362 terminal exit0; both automation tests Success.
  `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-v1-20260914/index.json`, SHA256
  `f5301e1b9f2de416482ee0af66e0fd1c9458d17fdbaa39d74151311b01f54d6d`.
- Serial native output `tmp/south-fork-reconstructed-cg-native-v1-20260914.bin`, SHA256
  `770d43899ecc02c3dd601decaf0ba5d9fcf51c5fad724a0ac1681c4d52257a95`.
- Independent serial audit55841 terminal exit0:
  `tmp/south-fork-reconstructed-cg-audit-v1-20260914.json`, SHA256
  `0d757d47c209ed7e76ee27a9675123cfa9e0c49bb9f7bedfe7275e0d08e91599`.
- Parallel engine22864 terminal exit0; both automation tests Success.
  `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-parallel-v1-20260914/index.json`, SHA256
  `55d50a672464509083cd09d5c9bd4c3416302def0c37dac1d77e28956c2444b6`.
- Parallel native output `tmp/south-fork-reconstructed-cg-native-parallel-v1-20260914.bin`, SHA256
  `e3e727bb0629a34ffec13332e71aa5fd6b984321a43b0e48f90d61e96d12e58e`.
- Independent parallel audit11087 terminal exit0:
  `tmp/south-fork-reconstructed-cg-parallel-audit-v1-20260914.json`, SHA256
  `1ea308be0152a2931e79bb46dd9f0036636c6af9975e68d557b79a4691977c13`.
- Final shader SHA256 `6d1dfbde89a4be8e0f77f9b87420afb98e62961fd01ecb573a1ad8badef0e754`;
  C++ test SHA256 `b696a13037691cd8f2f00c25f93024a1dc742df43b1fd47616d987920e4b8643`.
- Final combined regression suite: **139 tests pass8.10s**. Includes malformed
  native-output rejection, retained solve failures, tiny-value preservation,
  polynomial/physical-reference/reconstruction and30FPS runtime/release gates.

## Still open

These six static matrices do not qualify native reconstructed geometry/rates,
dry activation, complete nonlinear evolution, moving ownership, outer wave/foam
return coupling, contact or playable terrain/water/froth. Additional native
zero-RHS/degenerate/range/failure-path coverage and production cost remain.
No test-only solver was installed in gameplay or either running CPU history.

MAIN59896 remains live toward original9.066667139530182s and both moves;
last observed accepted0.39474369746687793s, maximumspeed21.56323m/s,13 rejected
trials in the current interval, mass residual-3.02647e-13m3. Earlier speed rose
to~27m/s then declined; this is not a stability/physical-acceptance claim.
Diagnostic95666 remains a separate old-failure-time prefix and is also live.
Both original dependency sets stay frozen until terminal/provenance handling.

Cook74818/PID41820 remains live, last observed7772s/local35440. Latest BOTH
audited7700s/local34000; next COMPLETE7800s/local36000 needs BOTH audits. Flow
remains unsettled. Desktop30FPS remains the target; latest playable measurement
18.899245FPS/p9570.33ms still fails. Full remaining-work scope remains active;
no scene acceptance, final commit or completed-goal claim.
