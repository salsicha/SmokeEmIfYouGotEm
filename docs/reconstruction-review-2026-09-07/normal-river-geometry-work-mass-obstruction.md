# Complete local geometry work and a mass-transport obstruction

September 14, 2026. Previous goal turn: PROGRESS (local auxiliary work identified
separately from the unresolved net energy defect). This continuation completes
the local reconstruction-work identity and proves that a momentum-only repair
cannot meet the nonbreaking energy gate with the current donor mass transport.
No playable or native solver promotion.

## Reconstruction energy transfer is now explicit

`physics/scripts/rational_geometry_energy_exchange.py` differentiates each W/V
factor row on its own local depth stencil. It retains the same represented
coefficient values, smooth rational polynomial, hydrostatic cuts, physical bed
slope, depth normalization and two inverse-metric factors. There are at most
nine local depth dependencies in 2-D (five in the one-dimensional profiles),
not an all-cells dense Jacobian or a globally fitted flux.

For row energy derivative J[row,depth], the explicit work at the row is
`sum_depth J[row,depth]*h_t[depth]`. Its reverse-gradient contribution belongs
to each corresponding depth cell. Each contribution is deposited at the row
and negated at that depth cell. This local graph transfer therefore satisfies

    explicit_geometry_work = geometry_gradient*h_t + geometry_exchange.

No mean subtraction, energy normalization, state mutation or omitted small
residual is used. Including the previous auxiliary exchange and the finite
stationarity residual r gives the full local identity

    e_t = E_h*h_t + E_p.p_t + geometry_exchange + auxiliary_exchange
          + sum(alpha*r.(z_t-q_t)).

The extra `-alpha*r.q_t` is retained: the exact inverse-action gradient uses Qz,
whereas the finite-solve stationary density uses (q-z)/beta. Their difference
must not be silently discarded in a claimed local identity.

This is energy bookkeeping for SUPPLIED rates, not a new conservative
hydrodynamic flux. The transfers do not remove net energy production or loss.
The mass/momentum flux pairing is still required, as is dry/open/breaking and
long-time qualification. No research timing here establishes 1.6 ms or 30 FPS.

## Independent checks and original-profile evidence

Initial test report `tmp/rational-geometry-energy-exchange-controls-v1-20260914.xml`
retains a development TypeError (constant divided by AD node). The implementation
was corrected to construct constant nodes; no physical gate was changed.
The v2 report has eight PASS in 2.26 s. Checks include:

- Independent forward factor-direction and existing reverse depth gradients.
- Complete cellwise work equality, local support, and unchanged input arrays.
- Singleton and two-cell periodic alias handling.
- Original rough, blocked/partial-cut pressure cases 7325 and 7326.

`tmp/south-fork-rational-geometry-energy-exchange-v1-20260914.json` records all
eight original physical profiles (64/128, seeds 2200/2202/2204/2206) with their
unchanged stress-stage directions. Source/bed hashes and 38 implementation
hashes are recorded; input and before/after implementation checks pass.

- Eight complete local identities PASS, worst error 2.1316282072803006e-14.
- Factor-value discrepancy <=7.93809462606987e-15.
- Independent forward-work discrepancy <=2.0539125955565396e-15.
- Independent reverse-gradient discrepancy <=3.630429290524262e-14.
- Geometry-transfer integral magnitude <=1.734723475976807e-17.
- All eight actual energy-conservation gates STILL FAIL, unchanged.

The prior full control set plus these eight tests produced 85 PASS / 25 FAIL in
51.37 s (`tmp/rational-geometry-energy-all-controls-v1-20260914.xml`). The same
25 earlier failures remain. Original-profile audit 75972 and suite 25130 are
terminal. This is numerical-control evidence, not a release or scene pass.

## Exact counterexample: changing momentum alone cannot work

Added `physics/tests/test_constant_velocity_mass_energy.py`. These are explicitly
manufactured controls, not replacements for the eight original profiles above.
Take flat periodic h=[1,2,4], dx=1/2, and constant physical velocity u=+/-1/2
along either axis. All cells are strictly wet, with no breaking closure.

For this exact constant mode, D u=E u=0, hence the same original two-pole metric
has E_p=u and E_h=g*h-|u|²/2. For ANY locally conservative momentum update,

    sum(E_p.p_t) = u.sum(p_t) = 0,
    E_t = g*sum(h*h_t)*dx²,

because total mass is also conserved. No choice of conservative momentum flux
can cancel a nonzero right-hand side while retaining this mass rate.

The independent Fraction-valued limiter oracle gives slopes [0,3/2,0]. For
u=+1/2 the current donor retained heights are [1,11/4,4], giving
h_t=[3,-7/4,-5/4] and E_t=-13.48875. For u=-1/2 they are [5/4,4,1], giving
h_t=[1/4,11/4,-3] and E_t=-15.328125. Production of this negative numerical
energy rate is not a proved physical breaking dissipation model. Nor does this
counterexample prove the cause of the older dry-bank speed explosions.

The actual research stage matches both exact rates on both axes to <1e-10,
preserves mass/momentum and satisfies the checked donor positivity bound.
`tmp/constant-velocity-mass-energy-v1-20260914.xml`: four oracle checks PASS;
four required nonbreaking energy-conservation checks FAIL, retained explicitly.
These are newly exposed failures, not four regressions caused by a solver edit.
The mass and momentum implementations have not been changed in this turn.

Final combined run including every prior control and these new controls:
`tmp/rational-geometry-mass-energy-all-controls-v1-20260914.xml`,
**89 PASS / 29 FAIL in 51.77 s**, process71205 terminal exit1. The previous25
failures and four newly exposed constant-velocity failures are all retained;
there are no skipped/xfail tests or relaxed tolerances.

## Next implementation and full goal

The next candidate MUST jointly replace the mass/pressure work pairing. A
momentum-only correction atop the unchanged donor mass is now ruled out by the
constant-mode identity, independently of the eight original energy failures.
Retain the original two-pole response, actual local geometry derivatives,
finite-depth/positivity requirements and all original profiles. A centered mass
swap alone was already shown insufficient; do not treat this counterexample
as evidence that such a swap solves the full problem. Any replacement needs
coupled conservation, regularity/refinement, variable-bed/dry/open and original
moving-source history checks before native/playable integration.

All five original jobs were directly checked live. The cook passed native
9372.5/local27450; complete9400/local28000 was not present on the filesystem
check. Latest BOTH-audited checkpoint remains9300; wait for the complete9400
marker before BOTH state and exterior-bank audits. Original 417/422 source
guards remain unchanged. No restart, suspension, history splice or source reset.

South Fork terrain/boulders/collision/hydraulics/waves/froth/contact and actual
desktop30FPS acceptance remain open. Troublemaker is still a rapid inside South
Fork, never a menu scenario. Colorado, Pacuare, Futaleufu, remaining Chilko/
Zambezi reviews, crew, normalization, regressions, release and final commit remain
in the full goal. No completion or unavailable visual measurement is claimed.
