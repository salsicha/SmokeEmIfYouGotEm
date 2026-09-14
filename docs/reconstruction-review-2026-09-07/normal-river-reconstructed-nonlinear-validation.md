# Reconstructed pressure: current and finite-amplitude checks

September14 UTC. Independent research comparisons; no native/gameplay changes.
The original-start South Fork requested-endpoint replay remains a separate,
unfinished qualification, not replaced by manufactured waves.

## Source and instantaneous nonlinear comparison

The solitary profile and its analytic time derivative use
[Guermond et al., equation7.1](https://people.tamu.edu/~guermond/PUBLICATIONS/GKPT_WaterWaves_2022.pdf).
For eta=a sech²(r(x-x0-ct)), h_t=-c h_x and (hu)_t=-c² h_x. The published
solution applies to standard SGN. Rational SGN has different governing
dispersion, so its discrepancy is not an exact-solution discretization error.
The parameters remain the earlier project comparison: h0=1.5m, a=0.45m,
x0=24m, periodic96m domain. Nonzero tails are truncated, not claimed an exact
periodic solution. No synthetic history is evidence of measured South Fork flow.

`audit_reconstructed_solitary_residual.py` compares those derivatives with actual
unscaled FV plus reconstructed pressure rates, retaining40 pressure iterations.
No solver, source or state repair occurred. Whole-domain mass and momentum
rates remain near roundoff; transverse momentum rate is exactly0.

| Model | dx | Relative momentum-rate L1 discrepancy | Largest pressure residual |
| --- | ---: | ---: | ---: |
| SGN | 0.5m | 0.0268568 | 7.23e-16 |
| SGN | 0.25m | 0.00688661 | 8.79e-10 |
| SGN | 0.125m | 0.00173637 | 1.97816e-5 |
| Rational SGN | 0.5m | 0.0340123 | 7.74e-16 |
| Rational SGN | 0.25m | 0.0168587 | 6.34e-9 |
| Rational SGN | 0.125m | 0.0131170 | **5.44643e-5 — FAIL** |

Standard SGN's rate discrepancy decreases approximately fourfold per refinement.
The rational model's finest pressure solve fails the unchanged2e-5 residual
gate; its rate discrepancy cannot be treated as a qualified fine-grid result.
The standard model's finest residual is also close to the limit. Better
linear-wave behavior does not establish sufficient iterative accuracy here.

Initial report `tmp/south-fork-reconstructed-solitary-residual-v1-20260914.json`
retained raw measurements but had no aggregate pressure-pass flag. The final
wrapper explicitly evaluates the existing residual gate and exits1 on the
fine-grid rational failure. Fresh retained report:
`tmp/south-fork-reconstructed-solitary-residual-v2-20260914.json`, SHA256
`52a7643c7021a282193b974016c50c35baba8f4ccdcd39f960ab910141983ef9`.
No tolerance or iteration limit was changed. This is not a history pass.

## Current and finite-amplitude histories are live

`audit_reconstructed_physical_history.py` preserves the original benchmarks:

- Current-wave session17326:2/4/12m wavelengths,32 cells/wavelength, FOUR
  wavelengths in the domain,0.4m/s current,1e-5m amplitude, one physical period
  at speed c+U. Original phase<0.03cycles/amplitude0.9–1.1 checks apply at four
  actual accepted-time checkpoints, with pressure residual<2e-5.
- Solitary session39791: standard SGN then rational SGN,0.5/0.25m grids,
  full96m domain and4s propagation. Retains waveform/peak/speed/momentum
  discrepancies; never labels rational comparison as exact-SGN convergence.

Both use original SSP-RK2/FV/CFL, unscaled shoreline reconstruction and120Hz
maximum step. Checkpoints neither change step sizes nor reset the interior.
Each run saves initial/final state hashes and final or failure `.case-N.npy`
states, progress JSONL and terminal report. Failed states remain failures.
Prefixes are `tmp/south-fork-reconstructed-current-wave-v1-20260914` and
`tmp/south-fork-reconstructed-solitary-v1-20260914`. Do not edit their audit,
shared helpers or solver dependencies while either is live.

StandardSGN0.5m now completed4s: relative surface L1 discrepancy0.0371006,
peak ratio0.991109, peak-speed discrepancy0.0148487, net momentum change
-1.34892e-14m3/s per width,481 accepted/0 rejected trials. Retained case0 state
hash is `d3a1bf9a08425c378f1b85ea9acf7263f08f8ac674f47fd7f044250497cd4773`.
The0.25m case is live; no convergence conclusion from the single finished grid.
Current2m case completed0.922955779s, phase0.00794282cycles/amplitude0.987858,
488 accepted/379 rejected trials, all four diagnostic checks pass. Current4m
case is live at0.349972s; neither process has completed its full suite.

Final relevant combined tests:99 pass6.34s. Coverage includes preserving
benchmark scope, source invariance, exact derivative, failed-state retention,
successful report serialization, and explicit fine-grid pressure failure.
Passing tests do not close the failed pressure gate or unfinished histories.

Full-river7600/local32000 passes BOTH state and artificial-bank audits, with
all86,720 artificial bank cells exactly dry. Outlet105.691269963 versus
inlet45.306954547m3/s remains unsettled. Same cook74818/PID41820 remains live;
next COMPLETE7700/local34000 requires BOTH audits. Main original-start59896
last accepted0.2416666771s, mass residual1.87e-13m3, still far short of the
required9.0666671395s/two ownership moves; no native-history promotion.

## Next boundary

Read terminal motion reports and original South Fork history without editing
their hashed dependencies. Diagnose the fine-grid rational solve's convergence
under the unchanged40-iteration/cost/residual requirements, not by relaxing
them. Continue independent variable-bed/wetting/outer-wave and foam return
coupling, native agreement, contact and playable-motion/performance checks.
30FPS remains the desktop target; latest gameplay18.899245FPS/p9570.33ms fails.
Terrain/rock/rapid fidelity, later rivers in the requested order, crew, release
and final completed-project commit all remain open.
