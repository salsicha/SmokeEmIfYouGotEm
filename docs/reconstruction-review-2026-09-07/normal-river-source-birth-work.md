# Original pressure work at a wetting front — September 15

This derives previously missing leading Hamiltonian derivatives at simultaneous
point births. It does **not** supply a complete front force, impulse law,
accepted dissipation, mass update, time integrator, native code or playable-water
acceptance. The nonlinear bank stage still rejects unresolved activation.

## Analytic coefficients

For source heights `k_i*e`, the original point storage gives
`V_i=R_i*e^3`, `R_i=c_i*k_i^3`. Old volume/momentum are fixed and newborn physical
velocities bounded. The established coupled pressure limit is
`E(e)-E(0)=e*S(k)+o(e)`. For each original pole, write
`C=I+beta*D`, `x=C^-1*v`, and `v=B.T*z_old`. Then

```
S(k) = -1/2 * sum(alpha*beta * v.T*x)
dS/dk_i = sum(-alpha*beta * v_i'.T*x
              + 1/2*alpha*beta^2 * x.T*D_i'*x)
lim e^2 * dE/dV_i = k_i/(3*R_i) * dS/dk_i
lim e * dE/dP_i = sum(alpha*x_i/sqrt(R_i))
```

`subcell_source_birth_work.py` evaluates these derivatives analytically. Both
volume roots in each original shared-face coefficient are differentiated,
including their repeated contribution when owner and target coincide. The
harmonic-column stage partials integrate the original logarithmic expression;
its moving wet-boundary term vanishes with the harmonic column. Equal stages
retain the continuous one-half stage partials, rather than differentiating an
arbitrarily selected minimum. Original small-difference series are retained.

The newborn factor derivative is contracted as
`sum((F*M*x).(F*M_i'*x))`, retaining original positive triangle factors and
ordered source faces. No finite-difference force, dense inverse, differentiated
pressure solve per source, eigenvalue repair, minimum water depth or energy projection is
introduced. The existing coupled solve exposes its response directly so the
work does not recover it through a cancellation-prone subtraction. Both original
poles and their unchanged 40-CG/residual gates remain in use.

Homogeneity requires `sum(k_i*dS/dk_i)=S`; the existing absolute 1e-10 chain-rule
gate is applied to this identity. It is an internal consistency check, not the
independent evidence for the derivatives.

## Why mass and momentum balance are not sufficient

Consider the conditional path `V_i=R_i*t`, `e=t^(1/3)`. It is a probe direction,
not a proposed physical update. The new volume-gradient work has leading term
`S/3 * t^(-2/3)`. Bounded newborn physical momentum rates contribute only
`O(t^(-1/3))` through canonical velocity, and bounded old rates cannot cancel
the stronger leading term. Bounded changes to old state of order t do not alter
the leading birth coefficient.

For nonzero S, simply appending the old bounded dry-front momentum flux cannot
give a conservative full-Hamiltonian birth update. This is **not** permission
to subtract that work as an invented dissipation budget. Its sign alone does
not derive an entropy law or a physical breaking mechanism. A compatible front
force/impulse or independently justified dissipation law remains necessary.

## Original South Fork evidence

The extended `audit_south_fork_simultaneous_birth.py` retains the earlier energy
and all-column pressure checks, then compares the new coefficients against the
original positive-water Hamiltonian's independently assembled volume gradient
and canonical velocity. Schema v2 records full coefficient/error vectors.

Original block [12,8], old 600-second snapshot: 16 existing pools, 24 cubic-volume
receiving source regions, four immediate new/new edges. Each of two directions
uses seven decreasing heights before all original source/face knots. The second
direction uses `k_i=cbrt(original_nondispersive_receipt_i/c_i)` to locate a
relevant probe, not to accept the old flux as the full model.

| Direction | Final volume-gradient max-norm relative error | Final canonical-velocity max-norm relative error |
| --- | ---: | ---: |
| Uniform stage | 3.074848e-5 | 9.703778e-7 |
| Original receipt direction | 4.969814e-5 | 2.812599e-6 |

Both errors refine by more than a factor of three and finish below the 1%
limit. These are vector max-norm controls, not relative guarantees for every
nearly zero individual component; complete vectors remain in the report.
Manufactured unequal-stage tests independently check individual derivatives.
Homogeneity error is zero in both bank directions. Maximum finite original
pressure residual is 2.621e-16, positive contraction error 2.221e-16.

The final audit also evaluates the **complete original base-rate direction**,
including old donor losses, new receiving momentum and original bed/wall forces.
Its independent net mass-rate error is 1.388e-16; boundary/bed momentum-rate
error 8.882e-16. Nevertheless, its full-Hamiltonian work scaled by `e^2`
converges to a nonzero value:

- Analytic coefficient: -2.0416723572359824e-5.
- Last original positive-water result: -2.0375323518328443e-5.
- Error: 0.202775%, down from absolute 1.749452e-6 to 4.140005e-8.

This measures the missing work even when those ordinary mass/momentum checks
pass. It does not mutate original water or grant an evolution pass. The existing
single-surface or engine solver is not switched to this research code.

Final report: `tmp/south-fork-source-birth-work-v2-20260915.json`, SHA256
`d5b806da8bead02ba73836af24f0c35aa4b6b76c918e561699bd6ee87dee3477`.
All 549 source/implementation hashes match at completion and recheck. Earlier
work-only v1 remains retained; v2 adds the original balanced-direction control.
All 464 protected source/terrain/capture/actor hashes remain unchanged.
The block has reflecting exterior cuts, not the natural open river. Provenance
remains 16 exposed-rock, four mixed exposed/inferred and four inferred-flank
receiving regions. Exact rational geometry adds no measurement precision.

## Verification and remaining scope

36 focused tests pass: 18 new work cases and 18 existing simultaneous/single
birth controls. Coverage includes independent 256-node harmonic partial
integration, equal/extremely unequal stage scales, independent finite energy
differences (test oracle only), original positive-water Hamiltonian gradients
at zero/nonzero bounded newborn velocity, single-source scaling, zero old
momentum, unchanged owned/stale/flat-case rejection, original balanced-rate
work and deliberately corrupted momentum-ledger rejection.

The final full source plus legacy-energy run reports 439 PASS / 13 retained
FAIL (153.12 seconds, terminal exit 1), including the added balanced-direction
case. Report: `tmp/source-birth-work-full-suite-v2-20260915.xml`.
All owned jobs are terminal.
No existing energy/geometry tolerance or failure is waived.

Next is to derive and integrate compatible physical front forces/impulses,
including edge/flat births and complete front transport; then verify finite time,
open boundaries and the native single playable surface. Do not remove the bank
activation guard or replace it with epsilon water. No engine visual/performance
change was made here: the last ordinary 12.361760 FPS / p95 93.2314 ms still
FAILS 30 FPS. South Fork wave/froth/reference qualification, Colorado → Pacuare
→ Futaleufu, all-scene water, crew, normalization, regressions and release remain open.
