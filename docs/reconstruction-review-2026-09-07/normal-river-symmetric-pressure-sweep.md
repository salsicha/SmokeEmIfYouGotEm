# Pressure convergence diagnosis and isolated symmetric sweep

September14 UTC. No running history, source, native mode, terrain or playable
material changed. The original block-preconditioned histories remain separate.

## The retained fine-grid failure is convergence-limited

`diagnose_reconstructed_pressure_convergence.py` captures the actual nonlinear
RHS for the original0.125m solitary source, without replacing its pressure solve.
The independently assembled sparse matrix matches the original factored action
to1.64e-16 relative error. Independent SciPy CG with the same preconditioner
and exactly40 iterations reproduces the larger-pole residual5.44643165e-5;
its solution differs from range-PCG by3.29e-16 relative. A direct matrix solve
reaches2.09e-15 residual. The scaled condition number is85.33 for the larger
pole versus9.90 for the smaller. This supports insufficient iterative convergence,
not a defect in the range normalization. The direct solve is a matrix reference,
not physical truth or an allowed runtime replacement.

Report `tmp/south-fork-reconstructed-pressure-convergence-v1-20260914.json`,
SHA256 `3e0870a6dea02b4a8ee240d4fb91f9b0101afa5dad78152aa9e570778f97568b`.
It records NumPy/SciPy versions and implementation hashes. The original failure
remains unqualified; no gate or iteration budget was increased.

## Isolated symmetric Gauss-Seidel preconditioner

New CPU-only `reconstructed_symmetric_sweep_reference.py` uses
M=(D+L)D^-1(D+L)^T for A=D+L+L^T, applying its inverse with two triangular
sweeps. Positive D makes this preconditioner symmetric positive definite.
The approach follows the symmetric-preconditioning principles described in
[Netlib's iterative-solver templates](https://www.netlib.org/templates/templates.html).
It changes only the preconditioner: CG still applies the original factored A,
keeps the actual RHS and checks the original true residual after40 iterations.
No source depths, rates, topology or accepted states are repaired or discarded.
The module is not installed in the existing adapter or any native pipeline.

Actual-RHS comparisons, larger pole:

| Case | Original residual | Symmetric sweep residual | Sweep solve wall time |
| --- | ---: | ---: | ---: |
|0.125m solitary,1536 unknowns|5.44643e-5 (FAIL)|9.52551e-13|58.6ms|
|2D variable bed,768 unknowns|6.75226e-6|3.12373e-8|60.1ms|
|Original South Fork source,32768 unknowns|5.05980e-8|1.25571e-13|737.4ms|

The small pole also passes in all three cases. The first two inputs are
manufactured physical FV states, not measured river motion. The captured case
uses the ORIGINAL first observation from
`tmp/south-fork-unscaled-owner-history-v1-20260914.json`, sourceSHA
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`,
including the original exterior state/bed, face velocity and temporal derivative
from its first real bracket, hybrid fraction and analytic dry activations.
It is an instantaneous solve, not a new history or interior reset.

Reports, all terminal exit0:

- `tmp/south-fork-reconstructed-symmetric-sweep-v1-20260914.json`, SHA256
  `df356e6d68dbc0203de0e35eb856e6c6219196bad51ab65c1074efaa1a0b39bd`.
- `tmp/south-fork-reconstructed-symmetric-sweep-2d-v1-20260914.json`, SHA256
  `e74913d25e56dfb26c46734f4a3ec8ae25276a3181241a00d564255bb23c92ef`.
- `tmp/south-fork-reconstructed-symmetric-sweep-captured-v1-20260914.json`,
  SHA256 `5999f60c148aa1a4d2a2da749fc55eb0685b762dedc3981fca8fa58bf989d7a0`.
  Session54268 terminal exit0;360800 stored triangular entries, build30.8/34.1ms,
  solves737.4/742.7ms. Both original captured poles already passed the residual
  gate; the new comparison improves accuracy but is NOT a cost pass.

These CPU costs fail the1.6ms production-solver requirement. No native or
30FPS acceptance follows from sparse reference success. Runtime-portable
preconditioning still needs design and verification, including dependency/cost
analysis for the serial sweeps. Do not install this expensive reference as the
playable solver merely to make the numerical gate green.

Ten new tests verify SPD/symmetry, dense-matrix agreement, unchanged fine action,
singleton/two-cell aliases,2D variable beds, fraction-zero rows, exact dry identity
and retained tiny positive coefficients. Capture scope restores the original
class after exceptions. Combined pressure/physical/30FPS/release suite109 tests
passes7.86s. This does not qualify evolving wetting or open-boundary histories.

## Concurrent physical histories

Current-wave17326 is now terminal exit0. The final report parses and confirms
unchanged implementation hashes and all three full-period/four-checkpoint
motion checks.2/4/12m final phase errors0.00794282/0.00571191/0.00410562 cycles,
amplitude ratios0.987858/0.991510/0.992683. All three final states are retained.
Report `tmp/south-fork-reconstructed-current-wave-v1-20260914.json`, SHA256
`0d87876d658bc0a0dd00cac566a404b4c70c56c8e0b8bf777e9e1001bd062ba4`.

Solitary39791 is still live. Both STANDARD SGN resolutions completed4s:
surface L1 discrepancy0.0371006→0.00954507 (ratio3.887), peak ratio0.991109→
1.000910, peak-speed discrepancy0.0148487→0.00272657, near-roundoff net momentum
change. Fine stateSHA `50206f9467624f99a0e295b87ddc106c444c6d6156507d0f162d6e26f408d240`.
This supports refinement in the truncated-periodic SGN experiment. It does not
make the SGN solitary wave an exact rational-model solution. Rational0.5m is
currently at3.00833s;0.25m and final suite/hash validation remain unfinished.

Main requested-history59896 last accepted0.2958333472s, interval3, one rejected
trial and accepted step1/240s. Maximum speed15.0070m/s and mass residual
-1.32644e-13m3. This is not the required9.0666671395s/two-move history; no resets
or preconditioner changes are applied to that live run. Diagnostic95666 remains
separate. Same full-river cook41820 last observed7633.5s; latest BOTH audited7600s,
next COMPLETE7700/local34000 needs BOTH audits. Flow still unsettled.

All source geometry, crest/froth return coupling, native/contact/motion/cost and
playable-reference requirements remain, followed by later rivers, crew and
release/final commit. Latest gameplay18.899245FPS/p9570.33ms still fails30FPS.
