# Compact exact addition and SM5 recovery

September 16, 2026. In progress; not package, visual, physical or 30 FPS acceptance.

Commit `d9aee8cac` adds a candidate integer-only binary32 addition helper and
independent tests. It remains separate from production arithmetic until actual
GPU comparison and shader integration checks complete. The wide exact Euler
and RK2 product/accumulation paths are not replaced by this two-operand helper.
No precision mode, iteration budget, platform target or acceptance gate changes.

## Arithmetic evidence

The Python Fraction oracle covers 64,078 input pairs: signed zero, subnormal
and normal boundaries, cancellation, rounding ties, large exponent differences,
overflow and invalid operands, plus seeded raw-bit random pairs. Nonfinite
operands retain the original helper's canonical-NaN policy, not general IEEE
infinity arithmetic. All 36 fixture tests pass, including comparison to NumPy
single-precision addition for every finite pair.

The MSVC control compiles the actual candidate shader include as C++, without
copying its algorithm. All 64,078 exact-rational expected bit patterns match.
Fixture `tmp/portable-add-fixture-v1-20260916.bin` SHA256:
`a2e0c655b1eea6ef5ea5cdcc3df73b9c69306e58460d30360c89a75931e59c54`.
The GPU test separately compares candidate and original wide-accumulator
addition to that oracle and checks input bit transport. Its execution is still
pending the editor build; CPU agreement is not GPU qualification.

## Compiler evidence

Private copies of the original failed preprocessed inputs preserve the original
compiler artifacts. FXC retains cs_5_0, O3, Zpr, Gec and Ni settings.

- Original-adder preparation with explicit `[unroll(2)]` annotations completed
  successfully (old session13666/PID15160 is terminal, not live). It remained
  expensive and reported register-pressure warnings.
- Compact-adder preparation WITHOUT explicit loop bounds failed X3511. The
  compact helper alone is not a demonstrated preparation fix.
- Compact-adder preparation WITH explicit two-iteration annotations completed
  successfully (session70263). Output SHA256:
  `252ce2d197174fc8b70c7c6071fae4c7f6e14f80b474e378439b7f16b9c4e5e2`.
- Pressure permutation9 with compact addition and explicit fixed loop bounds
  completed successfully in 29.455s. Report:
  `tmp/sm5-pressure9-add-bound-v1-20260916/report.json`.
- Pressure permutations2/4/11 completed successfully in35.647/94.946/89.503s;
  session96639 is terminal exit0. All four previously failed pressure inputs
  now have successful isolated compilations. Permutations4/11 have identical
  original and patched input hashes; this is not evidence of different code.
  Report `tmp/sm5-pressure-remaining-add-bound-v1-20260916/report.json`, SHA256
  `97f4849cb97fa973ead451d080b4332a5acee6dd0815c49253714f6c15acad77`.
- Transport21 remains session1965/PID19472. The other eight distinct failed
  transport inputs run sequentially in session27413, starting3 then4/9/10/
  14/15/16/22. Original byte-identical groups are3/27,4/28,9/33,10/34,14/20;
  15,16,21,22 are distinct. Original artifacts stay unchanged. The copied
  driver retains `pressure<N>` output filenames, but its source paths and
  report hashes identify transport shaders. No transport success yet claimed.

Warnings about signedness, shadowed loop variables and integer division remain
recorded. These isolated compiler results do not prove a full cook or SM5 GPU
execution. Production loop annotations and arithmetic remain unchanged here.
Editor build session87748/PID12368 is the existing two-worker build, not a
restarted job. At03:56:55 local it had completed106/160 actions. Session95612
waits for that exact process and requires its successful build log before
launching the candidate GPU comparison. Expected fresh output:
`tmp/portable-add-native-v1-20260916/index.json`. Do not launch a duplicate
editor or alter candidate shader inputs before this comparison finishes.

## Hydraulic checkpoint

The same live corrected-domain run18716/session69416 completed absolute1600s
(local8000). All 5,369,600 cells pass state/conservation checks; all 86,720
artificial-bank face cells remain exactly dry. Max depth4.505365274m, max speed
7.229039217m/s, volume3,005,822.574054599m3, max per-step mass residual
1.378528425e-8m3. Outflow87.916530431 vs inflow45.306954547m3/s rejects settling.

- State report `tmp/south-fork-context3-1600-snapshot-v1-20260916.json`, SHA256
  `6d3c358fd89d6de055a10a64e15e89d96c15b6dd1d3a00e0251cfeabd959f08b`.
- Bank report `tmp/south-fork-context3-1600-banks-v1-20260916.json`, SHA256
  `4d5ab046fb6d1ea0743d50c94e2ab72a1ddf720e72c815820417e250c4d3c6de`.

Continuation: completed local9000 / absolute1650s also passes all5,369,600
cell checks and all86,720 exact-dry artificial-bank face checks. Max depth
4.490972506m, max speed7.236992171m/s, volume3,003,663.384020110m3. Maximum
per-step conservation residual remains1.378528425e-8m3. Outflow89.099834811
versus inflow45.306954547m3/s still rejects settling.

- State report `tmp/south-fork-context3-1650-snapshot-v1-20260916.json`, SHA256
  `a3cc5ae6ca684a8ea808b692ee499de737989e29f9e673efbf1a80bfa6e8411a`.
- Bank report `tmp/south-fork-context3-1650-banks-v1-20260916.json`, SHA256
  `2c54b3c698e7d765e79d0107c10fb007b56ba4b97f201f1936381e05b92ddb15`.

Same editor build87748/PID12368 reached128/160 actions; queued GPU95612 has
not launched yet. Both transport compiler probes remain live with increasing
CPU time:21 session1965/PID19472 and3 session27413/PID24980. No restart or
production shader changes. Read-only inspection of the measured mesh-cost path
confirms persistent RHI allocation is already used; no new performance claim.

Next completed local10000 / absolute1700s needs both audits. No runtime-field,
geometry or normal-map promotion follows from the checkpoint. Ordinary play
still fails 30 FPS: last17.819710FPS / p9581.6343ms. Visible breaking and froth,
source-supported rock flanks, playable integration, all later rivers, crew,
physical regressions and release remain open. Troublemaker is only a rapid
within the South Fork scenario, never a separate menu entry.
