# Fixed-budget pressure-coordinate accuracy

September 18, 2026. Four retained research pressure-coordinate failures are
resolved on their original source states and frozen original directions. This
is not a native water, terrain, motion, visual, or 30 FPS acceptance result.
The nonlinear gameplay mode stays OFF.

## Cause and implementation

The original cell-local block-Jacobi derivative solve leaves residuals of
2.61e-8 to 3.85e-8 on the first pressure pole after the required 40 iterations.
These meet the looser pressure residual limit but fail the separate 1e-10
energy-coordinate identity. A two-pass full conjugacy-restoration experiment
on the unchanged four inputs reproduces essentially the same errors. Loss of
conjugacy is not the remedy; that experimental solve is not installed.

The research `block` preconditioner now uses symmetric block Gauss-Seidel.
For the unchanged matrix A=D+L+L^T, the preconditioner is
M=(D+L) D^-1 (D+L)^T. Forward and backward triangular sweeps apply its inverse.
Each diagonal block still contains exactly the original two velocity
components; off-diagonal blocks come from the original combined-alias factor
rows, including periodic wrap, both factor contributions, and dispersion
fractions. The original Schur block inverse is retained. There is no diagonal
shift, additional CG iteration, physical stencil removal, momentum/energy
projection, modified pole, or acceptance-threshold change.

The old local inverse remains explicitly available as `block-jacobi` at the
pressure-system API. Other preconditioner choices and the native solver are
unchanged. This Python reference implementation has no performance acceptance;
its triangular sweeps do more work per preconditioner call than local Jacobi.

## Same original inputs, not merely regenerated passing fixtures

`audit_pressure_block_sweeps.py` freezes the original geometry, velocity, mass
direction, and canonical-velocity direction under the old block-Jacobi path,
then evaluates both preconditioners on those identical arrays. All five input
hashes are checked after evaluation. The old failures remain explicit negative
controls, and the original failing test module is unchanged.

| Original seed | Old energy-coordinate error | Symmetric-block error |
| --- | ---: | ---: |
| 2201 | 3.7598912872e-10 | 1.1102230246e-16 |
| 2203 | 2.9071478558e-10 | 1.3322676296e-15 |
| 2205 | 1.9769019755e-9 | 3.5527136788e-15 |
| 2207 | 3.8196594498e-10 | 3.8857805862e-16 |

The gate is still 1e-10 times max(1, both work magnitudes). The largest new
first-pole derivative residual is 1.265064e-14. These are coordinate-identity
and solve checks, not a proof of nonlinear physical evolution.

Independent dense-matrix controls cover singleton/two-cell periodic aliases,
both axes and two-dimensional grids, variable beds, full/fractional/zero
dispersion, positive definiteness, symmetry, original-matrix equality,
multiple right-hand sides, input immutability, exactly dry identity columns,
and the unchanged iteration-budget guard. Final focused run: **25 PASS**.
The initial unchanged coordinate/patch group also passes all 11 tests.

The broader 14-module related group finishes with **145 PASS**, zero failures,
errors, or skips, in 550.85 seconds. It covers the original pressure/energy
operators, both coordinate bridges, one- and two-dimensional metric transport,
terrain transport, and wet-pool pressure. The prior 68-module physical suite
plus the original coordinate gate and new pressure controls finishes with
**902 PASS / 1 unchanged FAIL**, 903 tests in 389.63 seconds. The exact
float-storage/source-face discrepancy is still 1.77635684e-15; its exact
equality assertion remains enforced. This preconditioner does not change that
geometry API. The existing JUnit metadata warning is retained. The final dry
column control was added after this suite collected its tests and is verified
by the separate final 25-test run above. Neither selected suite is the whole
project or evidence that no other regressions remain.

## Hydraulic state and remaining delivery

The completed 8500/local16000 snapshot passes both full-state and artificial
bank audits: all 5,382,400 cells checked, all 86,720 artificial-bank cells
exactly dry, maximum depth 3.7882671734823106 m, maximum speed
5.352380686739509 m/s, maximum recorded step conservation residual
1.4754001131933592e-8 m3. Outflow is 98.9187544481 m3/s against
45.3069545472 m3/s inflow: **not settled**. Installed 4950 water is unchanged.
Cook 8900, start UTC 2026-09-18T06:34:59.2598919Z, remains the same live job.
The next 8550/local17000 snapshot has also completed and passed BOTH audits:
maximum depth 3.7865401190701427 m, maximum speed 5.35246432613662 m/s,
all artificial banks exactly dry, the same maximum step residual. Its outflow
is 103.1832767086 m3/s against the same inflow, so it too is NOT settled.
Next 8600/local18000 requires completion and both audits.

No engine material, source geometry, collision, hydraulic asset, map, menu,
crew, render quality, or gameplay timing was changed. The inspected put-in
imagery confirms an unresolved wooded-bank environment gap; no new bank or
canopy integration is claimed. Latest playable timing remains
23.476525 FPS / p95 52.3478 ms, FAIL against 30 FPS / 33.333333 ms.
Breaking/froth, physical coupling, refresh cost, and whole-river traversal
remain open, followed by Colorado, Pacuare, Futaleufu, Chilko/Zambezi reviews,
crew, normalization, outstanding regressions, and release checks.

## Evidence

The reproducible frozen-input audit is
`tmp/symmetric-pressure-frozen-original-v2-20260918.json`, SHA256
`077c9c331d781f5a96472d967558363299578b0e8ea081c7edf6170c33a5c558`.
It includes the input-array hashes and current source hashes. Independent
controls are `tmp/symmetric-pressure-independent-v2-20260918.xml`, SHA256
`82fb44c0b5aad65d4488e731de201c73da027ac79fc9bae9544ec2da4ea3ec41`.
Related group: `tmp/symmetric-pressure-related-v1-20260918.xml`, SHA256
`5f42a80e6e96d320f526035ef9f3953f772f1b4d79cc82c70d2ea41d1db4b6ac`.
Larger physical suite: `tmp/symmetric-pressure-full-suite-v1-20260918.xml`, SHA256
`9167c15488729f05202d145cf33052d90fb479ca92d403edc10d1ad7e0bdf901`.

Hydraulic reports are `tmp/control-ablation-{8500,8550}s-{state,banks}-v1-20260918.json`.
8500 depth SHA256:
`e580e561b5f2b1bc8e591472261cb8767214634c3f25fa8d07bfaa0ac3de29bf`.
8550 depth SHA256:
`0685b342f7ccc1244382ae604f08c8b4c956f99644f2adc3ee680ee25b9314bd`.
Generated binaries, data, and reports remain ignored local evidence.
