# Pressure cut-column derivation — September 14 UTC

Follow-up: [reconstructed pressure geometry](normal-river-reconstructed-pressure-geometry.md)
implements a static original-MC force/adjoint assembly, verifies its captured
wetting limit, and exposes a pressure-transfer accuracy limitation. It remains
research-only, with no candidate nonlinear solve or playable promotion.

The previous goal turn only reconfirmed the existing 30 FPS target and eight
parser tests; it did not advance the water integration. This continuation
rejects an invalid connection candidate and establishes a tested pressure-column
integration reference. No candidate is promoted to native or playable water.
The full requested project scope remains incomplete.

## Rejected harmonic connection

The unused `hydraulic_pressure_connections.py` candidate multiplied both
pressure interpolation weights on each edge by

`gamma = sqrt(4 fa^3 fb^3 / ((fa^3 + fb^3) (hi^3 + hj^3)))`.

That can preserve a divergence/negative-adjoint-gradient pair and `G(1)=0`,
but it does not preserve `D(1)=0`. On a flat, fully wet periodic bed, pressure
must not create net momentum. A reproducible counterexample uses NumPy RNG
seed20260914, h uniformly sampled from[0.4,2] on5x7 cells, a subsequent standard
normal pressure field, dx0.5, and fa=hi/fb=hj. Original depth-weighted pressure
gradient sum is[-2.6645352591e-15,-3.3306690739e-16]. Multiplying by gamma changes
it to[-2.051002946060499,-0.8266024156621109]. These are gradient sums; the
momentum force has the opposite sign. This is not a pressure-solve residual.

The candidate was never integrated. Its newly created, unused implementation
was removed; the formula and executable counterexample are retained here and
in `test_pressure_cut_face_reference.py`. Do not reinstate this weighting as
a qualified fix. No pre-existing solver, geometry or captured data was removed.

## Exact one-sided column integration

The existing pressure model reconstructs a quadratic column profile per density:

`p(s) = alpha (1-s) + beta (1-s^2)`, for0<=s<=1,

`alpha = 4B - 6P/H`, `beta = 6P/H - 3B`.

Here H is column height, P its integrated **nonhydrostatic** pressure, and B
its bottom nonhydrostatic pressure. This calculation does not add hydrostatic
gravity or assert that a real breaking flow follows this profile.

For a bottom cut retaining the top depth R, r=R/H, direct integration gives

`T = (3P-HB) r^2 + (HB-2P) r^3`.

The lower/blocked integral is **P-T**, not zero. T=P at full height, T=0 at
closure, and the derivative with respect to R vanishes at closure for a fixed
positive column and bounded pressure profile. Negative pressure is retained.
This regularity statement is not a uniform joint H->0 stability theorem.

`physics/scripts/pressure_cut_face_reference.py` evaluates the represented scalar
inputs with exact rational arithmetic and differentiates the same expression:

`r_t = (R_t-r H_t)/H`,

`T_t = P_t r^2(3-2r) - (H_t B+H B_t) r^2(1-r)`
`      + [6P r(1-r)+HB r(3r-2)] r_t`.

It returns both complementary integrals and rates. It imposes no depth floor,
pressure clipping or state repair. Dry H=0 has no normalized column and is
rejected. Outward tangents at R=0/H are rejected. Conversion to binary64 rejects
unrepresentable nonzero results rather than silently removing them. This slow
scalar reference is not a performance implementation or a pressure solver.

Tests independently integrate the quadratic with Simpson quadrature, check
moving-column derivatives by complex-step quadrature, exact complements,
full/closed faces, the quadratic closing limit, positive subnormal columns,
negative pressures and finite results despite overflowing H*B or P/H
intermediates. An initial approximate finite-cut derivative-ratio assertion
failed because it omitted the remaining cubic term; it was replaced with
exact coefficient identities, not a relaxed physics acceptance threshold.

## Captured South Fork edge

Authoritative derived report:
`tmp/south-fork-pressure-cut-column-v2-20260914.json`, SHA256
`01fb00b001be9ae7efd83adf55555c536aa94ac848720a98acc4d5382f9ff3be`.

Input is the previously completed
`tmp/south-fork-pressure-wetting-limit-v2-20260914.json`, SHA256
`dc8c0afd281a699810d38ec433d57889bfc19bb5f8156dcdd12506f6cb9b3ef4`.
The new audit verifies the original trace, binary and failed-history source
bytes against the input report's hashes before deriving its results. It does
not rerun the pressure solve or evolve a replacement history. Source hashes:

- Trace: `2cbfd26a98199bbbccd033d63e4d330f807e3de38aa5bbb6adf66b0aa1416723`.
- Binary: `21fe59c3cb20eb383662a8e23d323491926b9624393944e863b0f08783bc2a38`.
- History: `0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`.

In all four inspected brackets the reconstructed face-column heights equal
the corresponding cell heights exactly. The audit rejects unequal heights
rather than inventing a pressure reconstruction. The two one-sided integrals
are not identified as a shared numerical face flux.

At the narrowest bracket, the owner y22/x102 has H0.03481288m and opens from
R0 to7.8054086e-19m. Its actual solved pressure changes substantially:

| Owner-column quantity | Closed | Open |
| --- | --- | --- |
| Integrated pressure P | -0.000764714286 | 0.016934435501 |
| Top/retained integral T | 0 | 1.1406461e-35 |
| Lower/blocked integral | -0.000764714286 | 0.016934435501 |

Integrated quantities are per-density pressure integrals, not accelerations.
The blocked integral changes0.017699149787019038 even though the newly opened
top integral is negligible. Holding the left probe's P/B fixed while changing
only column/cut geometry instead gives T=-3.1643028e-37. This distinguishes
the regular geometric integral from the already discontinuous pressure solve.
The neighbor's full-height integral remains its own P and changes by
-6.3284227e-14. The original source force jump[0.14248036,0.46709793] is retained
as an unchanged observation, not reported as a force produced by this utility.

No time rates are measured in this snapshot audit. V1 is preserved but its zero
rate fields were default utility arguments, not source observations; V2 omits
those fields and explicitly records the rate scope.

This evidence rejects treating post-solve force clipping as a complete cure.
The geometry, shared pressure flux, force carried by blocked faces and pressure
equation must be derived together. The lower integral is not automatically the
net rock force: oriented faces and their differences still have to be assembled.
Do not add it on top of the existing B*bed-slope term without proving that the
same physical traction is not counted twice.

## Compatible-operator derivation boundary

One useful algebraic constraint for the next implementation is to write the
assembled pressure-gradient-plus-bed-traction operator as

`L(P,B) = -D^T P + E^T B`.

D maps horizontal velocity to the pressure model's divergence. E maps it to
the bottom kinematic component. The existing implementation uses a local
bed-slope dot product for E; a genuine cut-face traction may require a nonlocal
operator instead. D/E must be obtained from the physical face assembly, not
chosen solely to make the following matrix positive.

For q=Q-Da, c=Ea+C, and the existing per-pole constitutive pressures

`P = l (H^3 q + 1.5 H^2 c)`,
`B = l (1.5 H^2 q + 3 H c)`,

the acceleration matrix on positive-depth unknowns, normalized by M=diag(h),
has the completed-square form

`A = I + l (W^T W + 0.75 V^T V)`,
`W = (H^(3/2) D - 1.5 H^(1/2) E) M^(-1/2)`,
`V = H^(1/2) E M^(-1/2)`.

Here H denotes the diagonal depth matrix in the constitutive equations, not
an independently chosen cut height. The same cellwise breaking fraction can
be inserted between each factor and its transpose; its physical evolution
still needs separate qualification. This algebra is not a full nonlinear
energy theorem, a wet/dry proof, or permission to change the dispersion model.

For time-dependent geometry the material identities also require D_t and E_t.
Writing Adv for the consistently chosen horizontal advective acceleration:

`Q = (D u)^2 + D Adv - D_t u - u.grad(D u)`,
`C = E_t u + u.grad(E u) - E Adv`.

Thus replacing the force stencil alone is insufficient. Next derive the
second-order pressure-profile transfer and oriented face/blocked-traction
assembly on the ORIGINAL hydrostatic reconstruction, its negative-adjoint
kinematics and actual-FV-rate time derivative. Do not replace the requested
second-order model with a first-order toy or a geometry-reduced playable path.
Then test flat-bed momentum, variable-bed consistency, original wetting limit,
rough/dry lakes, thin films and full original-start stability/accuracy before
native, contact, presentation and cost qualification.

## Verification and unchanged project gates

Session83401 completes192 pressure/provenance/boundary/30FPS tests in16.91s.
This includes the prior145 tests and47 new tests; earlier54-test subsets overlap.
The pressure cut audit completes separately against current captured bytes.
No production physics, source geometry, timestep, scenario menu or fidelity
setting changed. The removed file was only the unintegrated rejected candidate.

Last actual gameplay remains18.899245FPS/p9570.33ms, failing desktop30FPS and
p9533.333ms. Physics120Hz and production solver1.6ms gates are unchanged.
Troublemaker remains a rapid within South Fork, not a menu scenario. No new
playable screenshot, reference-video inspection or completed-project commit.

Full-river continuation74818/PID41820 was directly verified live with increasing
CPU time, last observed local23220/native7161s. COMPLETE7200/local24000 is absent;
both audits remain due when it completes. The latest completed audited snapshot
remains7100s. No cook restart, pause or source promotion occurred.
