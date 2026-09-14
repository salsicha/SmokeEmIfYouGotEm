# Equivalent positive physical energy, without the dense inverse metric

September14,2026. Previous turn: PROGRESS (local physical momentum stress,
reversal correction in controls, retained energy failures). This turn derives
and implements an equivalent physical-energy realization and connects it to
the same unqualified stress component. No full-goal acceptance is asserted.

## Same model, different algebraic realization

Let Q=WᵀW+3VᵀV/4 be the existing reconstructed nonbreaking pressure operator.
Both original poles use this SAME Q. The original normalized mobility is

    S=cI+w1*(I+lambda1*Q)^-1+w2*(I+lambda2*Q)^-1,
    c=1-sum(original stored weights).

Its inverse, required for physical-momentum energy, is exactly the rational
function

    K=S^-1=k0*I+alpha1*Q*(I+beta1*Q)^-1+alpha2*Q*(I+beta2*Q)^-1.

The new factors are derived from the original represented numbers using
80-digit arithmetic, not fitted to profiles or substituted for the wave model:

- k0=1.0; exact represented zero-frequency response is1.
- beta1=0.10059130463209877, beta2=0.010519806479012348.
- alpha1=0.20778626364959746, alpha2=0.12554706968373586.

For verification, write the original scalar S(x)=N(x)/D(x), where
D=(1+lambda1*x)*(1+lambda2*x). Form N directly from c,w1,w2 and factor
N/N(0)=(1+beta1*x)*(1+beta2*x). Matching the two remaining numerator
coefficients yields the alpha values. Tests check K(x)*S(x) against1 from
x=0 through x=1e12. This equivalence relies on common Q; it does not authorize
changing geometry, pressure weights, breaking fractions or boundary operators.

## Positive local auxiliary energy and its direct derivative

`physics/scripts/rational_primal_energy.py` takes physical momentum p exactly
as supplied. For q=p/sqrt(h), solve z_j=(I+beta_j*Q)^-1*q with the original
40-CG budget and same full factored operators, using patch preconditioning.
Then Kq=k0*q+sum(alpha_j*Qz_j). Qz is computed with the W/V actions, not by
subtracting near-equal q and z values. No dense S inverse is constructed.

The kinetic energy is a sum of nonnegative local contributions:

    E_kin = k0*||q||²/2
            + sum_j alpha_j/2*(||Wz_j||²+3||Vz_j||²/4+beta_j*||Qz_j||²).

Cell area is applied to the total. It agrees with qᵀKq/2 up to solve error.
Equivalently, the j contribution is the stationary minimum of
alpha_j/2*(zᵀQz+||q-z||²/beta_j); its stationary equation is the same pole
solve. This local auxiliary representation is a basis for deriving compatible
stress work. **Positive energy does not prove convexity, conserved energy,
entropy stability, positive time evolution, or a valid breaking closure.**

At fixed physical p, differentiate q=p/sqrt(h) and use
K_h=sum(alpha_j*A_j^-1*Q_h*A_j^-1). The explicit tangent and local reverse
gradient implement these terms directly. The reverse coefficient accumulation
was factored into `factor_depth_gradient`; the old dual path still supplies
its original negative weight*length, while the new primal path supplies
positive alpha. Defaults and old arithmetic order are preserved and tested.
The forward derivative, dense original metric derivative and original dual
Legendre gradient provide independent checks.

## Original-state evidence

`tmp/rational-primal-energy-controls-v1-20260914.xml`:25PASS,6.13s.
New controls include scalar inverse identity, three multidimensional/short-axis
dense metric comparisons, original rough blocked/partial-cut cases7325/7326,
constant physical velocity, independent fixed-p finite differences, derivative
and round-trip checks. Original reverse/geometry tests also pass.

`tmp/south-fork-rational-primal-energy-v1-20260914.json`: all16 original
64/128 physical states, including variable beds; physical source momentum is
the input and mass direction uses its original velocity, without a reset.

- All16 independent chain-rule gates and all16 final directional gates PASS.
- Maximum canonical velocity error versus original dense K:4.951594689828198e-14.
- Maximum energy difference:7.105427357601002e-15.
- Maximum physical momentum round-trip error:1.0658141036401503e-14.
- Maximum fixed-p gradient difference versus original Legendre reference:
  1.865174681370263e-13; independent chain-rule error1.1102230246251565e-15.
- Worst final finite-difference energy error8.62405258317267e-10, below1e-7.
- Maximum inverse-metric solve residual3.005408934012525e-15.
- Minimum sampled local kinetic density0.7494181459313733 (these profiles only).

Shared-load timings average0.8448097s for the original dense metric reference
versus0.1008053s for the new physical energy plus directional evaluation.
These are different reference tasks, not a like-for-like full-stage speedup,
native benchmark or1.6ms/30FPS pass. No production performance claim follows.
The report checks implementation hashes before and after execution.

## Connected to physical-state stress entry, not gameplay

`conservative_rational_stress.stress_stage_physical` now prepares canonical
velocity from physical momentum with the equivalent matrix-free realization,
then calls the SAME conservative stress component. It checks the physical
momentum round-trip and leaves h, bed and p unchanged. A failed tolerance
rejects the preparation; no mean correction, scaling, mass floor or reset.
The existing canonical entry and dense audit control remain available.

`tmp/south-fork-conservative-stress-primal-entry-v1-20260914.json`: all8
original flat profiles still pass physical momentum conservation and **all8
still FAIL energy conservation**. Maximum source velocity recovery error
5.773159728050814e-15, local physical-flux error1.1457501614131615e-13.
This confirms equivalent state preparation, not an energy fix. New tests
compare the physical entry to dense preparation and require unchanged inputs.

Final `tmp/rational-primal-integrated-controls-v1-20260914.xml`:
**67PASS/25FAIL,52.19s**, process34426 terminal exit1. Failures remain8 stress
energy controls,13 original momentum/rest/reversal/reflection controls, and4
original cell-block accuracy controls. No xfail or weaker gate. New short
audits and tests are all terminal; original histories/cook remain separate.

## Next real correction and full scope

Use the explicit auxiliary energy and stationarity identities to derive a
local stress/positive-transport work balance. The previously measured stress
and donor-mass energy defects remain; neither a centered-mass-only swap nor
global projection is acceptable. The positive primitive handles the current
positive periodic reconstructed geometry, but the stress component still
rejects variable bed, and no dry/open/long-time/breaking qualification exists.
Do not feed captured dry source cells through a floor to make them admissible.

All five original handles were directly checked live this continuation; no
source/history reset or restart.417/422 guarded source files each check unchanged.
The cook was directly awaited through COMPLETE9300/local26000, then BOTH
`tmp/south-fork-expanded-9300s-{state,banks}-v1-20260914.json` audits passed.
5,382,400 finite cells;86,720 artificial-bank cells exactly dry. Maximum depth
3.7807176436051275m, speed6.233777917517893m/s, volume2550319.1771818926m3,
snapshot/driver volume discrepancy0, maximum step residual1.4535885384248104e-8m3.
Outflow102.60874739872392 versus inflow45.30695454719997m3/s remains unsettled.
Depth SHA256 `4ae9dfaeb4e088beabae07045ce5bbe54abb52e03a18a76ea2867c441db87246`.
Original83142 remains live beyond9301.5; next complete9400/local28000 requires
both audits. Full South
Fork terrain/boulder/collision/hydraulics/wave/froth/contact and30FPS acceptance
remain open, followed by Colorado, Pacuare, Futaleufu, other-scene/crew reviews,
normalization/regressions/release/final commit. Troublemaker remains an embedded
South Fork rapid, not a scenario. No native/gameplay promotion or completion.
