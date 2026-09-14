# Local physical momentum stress; energy split still incomplete

September14,2026. Previous turn: PROGRESS (analytic coordinate bridge,
same-operator preconditioning and9200 checkpoint audits). This turn removes
the unresolved primal-reference noise and implements a conservative stress
component. The full river/gameplay objective remains OPEN; this is not a
flat-bed substitute for variable-bed reconstruction or the requested scenes.

## Same wave operators, better independent primal reference

`rational_dual_energy_reference.evaluate` now has an explicit optional
`preconditioner='patch'`. Default remains original `block`; both original
pole operators, constants and40-CG iteration budget are unchanged. The
physical-rate bridge and audit can explicitly select primal and derivative
preconditioners independently. Nothing switches an existing stage/history.

`tmp/rational-fullpatch-controls-v1-20260914.xml`:13PASS. New controls compare
the primal auxiliary solutions directly with independently assembled dense
original operators on three shapes, check the depth tangent, original default
behavior and rejection of unknown schemes.

`tmp/south-fork-rational-physical-rate-fullpatch-v1-20260914.json`: original
16 source profiles and original canonical stage directions, patch primal
and derivative solves. Worst final pointwise finite-difference discrepancy
falls from6.1519329319637e-7 (original primal reference) to
**3.0011060303536397e-10**. All16 energy-coordinate gates pass, worst
3.9968028886505635e-15; worst primal residual1.4250853425550618e-14.
The former128-cell discrepancy was not evidence of a missing analytic
derivative term. Momentum failures of the old coupled stage remain.

The fullpatch report hashes precede a later optional exposure of auxiliary
rates by the bridge for the new stress component. That output option adds no
arithmetic change to the old default path. The subsequent stress reports
hash the later implementation. No report is relabeled as another version.

## New local momentum-stress component

`physics/scripts/conservative_rational_stress.py` is explicitly positive,
periodic and flat-bed only. Variable-bed inputs are rejected, not flattened;
dry/open/history/entropy/gameplay are unqualified. It retains the positive
continuous-envelope donor MASS operator and both pressure poles, while
replacing the donor-dependent pressure transpose with a local stress flux.

For continuum flat-bed auxiliary velocities z_j, d_j=div(z_j), the stationary
local dual kinetic representation is

    H_local = c*h*|v|²/2
              + sum_j w_j*h*(v.z_j-|z_j|²/2-lambda_j*h²*d_j²/2)
              + g*h²/2.

Its continuum translation stress is

    tau_mn = h*v_m*u_n
             + delta_mn*(g*h²/2-sum_j w_j*lambda_j*h³*d_j²)
             - sum_j w_j*lambda_j*h³*d_j*partial_m(z_j,n).

This is an auxiliary-field continuum derivation, NOT a proof of the current
discrete energy balance. The code uses the registered reconstructed flat
divergence and centered cross derivatives, then averages node stresses onto
faces. Canonical momentum m=h*v evolves by the negative face divergence.
The old positive donor depth rate remains unchanged; v_t follows the product
rule from that m_t and h_t. No state or global momentum projection occurs.

The **physical** local momentum rate is not identified with m_t. On the
registered flat geometry, with C_j=h³*D(z_j), the exact discrete identity is

    p_m = m_m + directional_divergence_m(B_m),
    B_m(face) = sum_j w_j*lambda_j*(other*C_j,owner + own*C_j,neighbor).

This follows from the actual weighted D transpose and the auxiliary pole
equations. Differentiate all weights, h powers, kinematics and auxiliary
velocities using the analytic bridge. The physical momentum flux is the
canonical stress flux minus B_t on its diagonal. Hence its negative
divergence reproduces the full physical p_t locally, up to pole-solve error.
This is a face identity, not an integral-only correction. Floating range
errors in the new stress products reject the calculation, not repair depths.

## Results and retained failure

`tmp/conservative-rational-stress-v1-20260914.xml`:8PASS. Controls cover local
physical flux closure on four1-D/2-D/short-axis shapes, mass-only positive
forward-Euler bounds, resting reflection and near-zero reversal in both axes,
and the original **two-pole** linear Fourier response at finite kh. These
checks do not prove coupled time positivity, nonlinear wave accuracy or banks.

`tmp/south-fork-conservative-rational-stress-v1-20260914.json` uses the same
eight original64/128 flat profiles. All8 physical momentum tests now PASS;
worst integrated rate2.6367796834847468e-15, worst local face-flux discrepancy
1.4566126083082054e-13. Source physical velocities are recovered through the
same two-pole metric, not replaced. The previously measured43.491m/s² reversal
jump is absent in the new component controls. The old model/tests are retained.

**All8 separate energy gates FAIL.** At64 cells, rates for2200/2202/2204/2206
are0.0078018143561,-0.0019853244423,-0.0042390743370,0.0007864435106.
Both signs occur: this cannot be treated as a qualified dissipative closure.
Reports include energy rate per unit transverse width because the single-cell
width changes with resolution. Do not disguise this mismatch as a CG issue:
energy-coordinate closure remains approximately roundoff.

Initial combined `tmp/conservative-rational-stress-combined-v1-20260914.xml`:
29PASS/8FAIL,21.82s; all failures are the independent energy requirements.
The final broader v2 suite also retains the original donor-stage momentum,
reversal/reflection and original cell-block accuracy failures.

Final `tmp/conservative-rational-stress-all-controls-v2-20260914.xml`:
**58PASS/25FAIL,51.59s**, process75348 terminal exit1. The failures are8 new
stress-energy controls plus17 original physical/accuracy controls; none was
waived. Process47591 completed the v2 stress/work-decomposition audit. All
new short jobs are terminal; the original five histories/cook remain separate.

## Energy-work decomposition determines the next correction

The v2 stress audit adds a diagnostic-only work split. At fixed canonical
momentum m, chi=H_h-u.v. With canonical stress rate m_t, energy work is
chi*h_t+u.m_t. The code separately reports the work with a centered physical
mass-flux derivative and the incremental work of the actual donor mass rate.
**Actual transport remains positive donor transport throughout.**

Example seed2200/64: centered-control work0.003935619448293348 plus donor
increment0.0038661949078020444 equals0.0078018143560956155 to roundoff.
For2202/128 the centered control is positive2.2266248168589797e-5 while the
donor increment is negative-0.00022852645352044754. Thus merely centering
the mass flux does not fix the stress's discrete work, and the donor increment
is not uniformly dissipative. The next implementation needs a compatible
local discrete product/work split for **both** stress and positive mass
transport; do not apply a global energy projection, weaker gate, depth floor,
or a centered-mass-only replacement. Variable bed forces and exact-dry support
must then be derived on the full requested geometry, not skipped.

## Full objective and provenance

No native map, terrain, material, gameplay scenario, captured source or
in-flight history was changed. Original417/422 file guards check unchanged.
All five original jobs were directly confirmed live this continuation. The
latest complete dual-audited cook is9200/local24000 and remains unsettled;
9300/local26000 requires BOTH audits after completion. Source and10000 target
remain unchanged. Terrain/boulders/collision/waves/froth/native contact and
30FPS acceptance remain open, followed by Colorado, Pacuare, Futaleufu,
other-scene/crew reviews, normalization/regressions/release/commit. Troublemaker
remains a rapid inside South Fork, not a scenario. No completion claim.
