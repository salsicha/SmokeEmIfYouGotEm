# Native CG repeated layout comparison: accuracy retained, timing variable

September14,2026,08:19UTC. Sixty complete original-source GPU solves pass all
existing gates with identical solution/diagnostic bits across layouts and repeats.
The slot-major layout is faster in the recorded comparisons, but timings vary
dramatically during the run. Neither the earlier52.5ms samples nor the new3.8ms
samples establish stable production cost or30FPS. No gameplay promotion.

## Batched-load experiment: no measured improvement

Added an opt-in four-entry load batch to phases3/6. Products are fetched ahead
but accumulated in the original row order; FP64, every coefficient, source and
all40 iterations remain unchanged. Batched source outputs and diagnostics for
all six cases are bit-exact to the independently audited original CSR run.

However, captured pole samples are53.146/53.225ms versus earlier slot-major
52.501/52.495ms. This does not demonstrate an improvement. The option remains
disabled by default and is NOT selected by the paired-layout benchmark. No
performance benefit is claimed. Build91287 exit0/15.70s, engine11289 exit0;
both native GPU regression tests pass.

## Repeated interleaved measurement

New explicit `-RaftSimReconstructedCGPairedLayouts` runs all six original cases
ten times in one process: CSR,slot,CSR,slot,... . Each layout's first run is
retained as warmup, leaving four measured samples per layout/case. Per-phase
queries are disabled in this mode; outer solve timestamps remain. All60 solves
retain40 iterations and original accuracy checks. Every later GPU solution and
diagnostic is compared bitwise with that case's first CSR result. The last six
solutions retain the existing binary format for independent external checking.

Build62730 exit0/15.96s. Engine89222 exit0; both automation tests pass. All60
records are present, all checks pass, and all repeated GPU bits match. The final
six native CPU/GPU outputs and diagnostics independently match the earlier
PASSED original factored-operator audit's referenced output, after verifying its
SHA. Thus no changed problem or relaxed tolerance explains the timings.

Original South Fork,32768 unknowns and328032 real entries per pole:

| Pole/layout | Four post-warmup samples(ms), in observed order | Mean(ms) |
| --- | --- | ---: |
| Larger,CSR |7.601,7.605,7.608,55.257 |19.51775 |
| Larger,slot-major |3.821,3.818,7.245,21.561 |9.11125 |
| Smaller,CSR |7.608,7.608,10.305,55.279 |20.20000 |
| Smaller,slot-major |3.850,3.825,21.335,21.830 |12.71000 |

The first CSR warmup took126.775/126.397ms; the first slot warmup took
3.816/3.847ms. Samples later in the run slowed substantially for BOTH layouts;
small1D/2D cases also changed from~1.6-1.8ms to~3.6-4.3ms. Retain the complete
sequence, not only fast values. These are shared-load editor component samples,
not whole-frame timing. Geometry/RHS assembly, two-pole combination, evolution,
contact and scene rendering are still excluded. No runtime cost gate is passed.

Read-only post-run `nvidia-smi` reports RTX3060 Laptop GPU,P3,1702MHz graphics/SM,
6001MHz memory,0% utilization,44C,22.76W at local01:21:49.977. This is AFTER the
run, not contemporaneous evidence of its clock/thermal/utilization changes.
It does NOT diagnose the cause of the timing variation. No GPU settings changed.
NEXT: correlate per-solve timing with during-run GPU clocks/power/utilization and
host submission timing, preserving all results. Do not choose only fast samples
or infer thermal/power throttling from the post-run snapshot.

## Artifacts

- Original fixture unchanged, SHA256
  `4e53b1bab29626585d3d017408d9043956fa61f5077cc55cd4087f1229a6feb4`.
- Batched output `tmp/south-fork-reconstructed-cg-batched-loads-native-v1-20260914.bin`, SHA256
  `c600f34239bb7bf787dd42c7c4be5f07d142b5e482381bbcdb3fd5de29767f8a`.
- Batched report `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-batched-loads-v1-20260914/index.json`, SHA256
  `43497d7b5d0ffad30f8731a7deae140f4510f0fdfcd1346026ef9d4e293c9eaa`.
- Paired output `tmp/south-fork-reconstructed-cg-paired-layouts-native-v1-20260914.bin`, SHA256
  `34176f76b26d749e7dcdfc759ce66407c021e5350a4b170e12251362e660c16e`.
- Paired report `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-paired-layouts-v1-20260914/index.json`, SHA256
  `f9dee093fb0e37ce6c022b7574b87a0c69339ac2a2dd3f42e040dcb67e5c5885`.
- Final shader SHA256 `675ba1a2ffabd604adc977118ebc3a0fa386a9b92dc160d17f73e92fcebeb2ca`;
  C++ test SHA256 `49fab01a4fe3a65afc0cb4ca571b0c921f8164a6412094aceb1a7c67376b998b`.
- All new builds/engine processes are terminal. No Python or live-source
  dependencies were edited. Previous139-test Python pass remains the latest;
  current checks are the two native regression runs and exact-output comparisons.

## Full scope remains open

MAIN59896 remains live, last accepted0.4415827887064084s with24 rejected trials
in that interval and mass residual-4.12670e-13m3. Full original9.066667139530182s
and both moves are still unproved. Diagnostic95666 remains a separate live
old-failure-time prefix. Keep both dependency sets frozen.

Cook74818/PID41820 remains live, last observed7846.5s. Latest BOTH audited7800s;
next COMPLETE7900/local38000 requires BOTH audits. The flow remains unsettled.
Native geometry/rates/range/degenerate cases, evolved physics/ownership, outer
wave/foam coupling, terrain/contact/playable integration, other rivers, crew,
regressions/release and final commit remain open. Latest actual playable
18.899245FPS/p9570.33ms still fails30FPS. No scene or completed-goal claim.
