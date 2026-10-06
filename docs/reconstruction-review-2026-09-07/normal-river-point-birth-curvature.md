# Point-birth curvature: guarded singularity and actual edge inventory

September 15. This derives a limit of the **existing guarded common-trace
expression**, not a justified wet-front curvature law. Source activation and
unequal-support guards remain intact. No pressure pole, terrain, water state,
native default, material or playable scenario is changed.

The previous metric/geometry-time coefficients do not by themselves complete
the nonlinear front force. The curvature expression can have a leading
singularity in manufactured crease cases. On the retained South Fork bank,
the relevant old/new edges instead have a zero leading coefficient. Eight
newborn/still-dry internal curvature edges remain unresolved; they are not
silently counted as complete forces.

## Conditional original-expression limit

For exact source heights `k_i*e`, `V_new_i=r_i^2*e^3`, retain the original
coupled pressure response. Write `a_i=lim e*w_i` and
`d_i=lim e^2*div(w)_i=N*a`, where `N/e` is the physical new/new divergence.
Consider an original slope-jump edge between old water and a newborn source.
If old depth at the source minimum is `H>0` and the wet edge grows by `L*e`,
the current arithmetic mean-depth trace has

```
lim integral(mean_depth^2)/e = L*H^2/4 = m2
coefficient = -3*m2*d_new/4
lim e^2*(N(w)*w) on EACH owner = coefficient*Hessian*a_new/4
lim e*(N(w)*u)_new = coefficient*Hessian*(u_old+u_new)/4
```

`Hessian` is the original normal slope jump times the normal outer product.
The first two factors of one-half come from the existing divergence/velocity
traces and owner distribution. The slope-dot-velocity term is lower order.
Old/old and immediate new/new edges do not contribute to this `e^-2` limit.
Original sloping-face endpoints determine `L`; delayed contacts are not moved
to the source minimum. Tangential slope continuity is checked with the exact
represented source coordinates before forming the rank-one Hessian.

The pressure pullback is still essential: `T.T*N(w)*u` has an order-`e^-2`
old contribution from its singular newborn right-hand side. Using the same
notation as the preceding connection derivation, solve
`y=(I+beta*D_new)^-1*(newborn_rhs/r)`. The old coefficient is
`-beta*R_old*(I+beta*Q_old)^-1*B*y`. Subtract the independently assembled
`N(w)*w` coefficients on both blocks and sum the original positive pole
weights. Matrix-free original factors, 40-CG / 2e-5 residual and absolute
1e-10 analytic skew-work gates remain; no force remainder or energy projection
is introduced.

`subcell_point_birth_curvature.py` returns this conditional RHS coefficient,
not physical acceleration. A singular individual expression does not prove
the complete equation diverges, nor justify discarding the term. The missing
front trace and joint dynamics still require derivation and verification.

## Manufactured evidence and retained failures

Independent finite-water calculations use the unchanged `SourceCurvatureTensor`
and original pressure solves. Both coordinate axes, nonzero/zero bounded
newborn velocities and both orientations of an oblique same-cell edge are
checked. Nonzero crease coefficients refine to the analytic vector; the
planar control remains exactly zero. One oblique orientation has zero leading
newborn divergence and therefore a zero leading coefficient despite a nonzero
slope jump. That zero is retained, not replaced by a convenient nonzero case.

The first run had 5 PASS / two insufficient-refinement failures at the fixed
2e-7 absolute vector tolerance. Two smaller positive-water probes were added;
the original tolerance was not changed. The next run retained an incorrect
test expectation that both oblique orientations have a nonzero leading force.
Final tests explicitly preserve the zero-divergence orientation and verify its
independent finite expression. Earlier v1/v2 reports remain under `tmp/`.

Focused-v3: 63 PASS. Final new module: 11 PASS, including path scaling
`coefficient(3*k)=coefficient(k)/9`, zero old motion, unchanged original state,
complete edge-count classification, invalid velocity, corrupted original
pullback residual and independent corrupted-vector rejection. The actual
nonlinear stage still rejects the unequal-support test front.

## Actual South Fork bank: zero leading coefficient, eight open fronts

Source-locked schema v5 retains original block [12,8], the 600-second snapshot,
16 old pools and 24 receiving point-source regions. Each of two paths has
seven decreasing heights. All prior energy, full-column operator, pressure,
metric-force and connection controls remain.

The 33 original old/new faces partition exactly into:

- 24 equal-source-slope faces;
- nine faces whose old water surface is at or below the newborn source minimum;
- zero contributing immediate slope-jump edges.

Thus the guarded expression's `e^-2` coefficient is zero for both bank paths.
The finite expression's scaled maximum absolute errors decrease:

| Path | First error | Final error |
| --- | ---: | ---: |
| Uniform stage | 8.456348e-14 | 2.064539e-17 |
| Original receipt direction | 3.130293e-11 | 7.642326e-15 |

Zero coefficients use an absolute 1e-10 check, not a relative error against
zero; nonzero coefficients require less than 1% relative max-norm error.
Both cases must refine by more than three unless the finite expression is
identically zero. Maximum original solve residual is 3.347e-16; maximum
unscaled finite skew-work residual is 6.903e-17. These are diagnostics of the
guarded expression, not full front-energy/time acceptance.

Crucially, **eight unresolved internal curvature edges remain at every probe**.
Their owned sides are newborn pool indices 17, 18, 21, 22, 24, 31 and 32
(index 17 has two edges). Their other source regions remain unowned/dry.
The full records preserve both original source IDs. The next coupling work
must account for these interfaces, not infer full curvature completion from
the zero immediate old/new coefficient or remove an activation guard.

Final report: `tmp/south-fork-point-birth-curvature-v2-20260915.json`, SHA256
`06c629f983e1adf0c1a3907a6b2811b6537c566da0907d2a5b4301c5026f8a44`.
All 559 source/implementation hashes and 464 protected source/actor hashes
match. Receiving provenance remains 16 exposed-rock, four mixed
exposed/inferred and four inferred-flank regions. Reflecting block cuts are
not the open river; exact arithmetic adds no measurement precision.

## Remaining work and reference cross-check

Full retained source/legacy-energy suite: **508 PASS / 13 unchanged FAIL**,
zero errors/skips, 116.23 seconds, terminal exit 1. Failure identities exactly
match the preceding 497 PASS / 13 FAIL run: one legacy source-face rounding
consistency failure, eight paired-stress energy failures and four constant-
velocity energy failures. The existing JUnit record-property compatibility
warning remains. No gate is waived. Report:
`tmp/point-birth-curvature-full-suite-v1-20260915.xml`, SHA256
`503ce6174bd8ffb6dcea5d5e16f0f482d3e708bff12081936d139409848ed768`.
All owned audit/test jobs are terminal.

A literature cross-check of Guermond, Kees, Popov and Tovar, sections 1–2,
confirms their method uses a hyperbolic relaxation of the SGN model with
continuous finite elements. It is not a derivation of this project's original
rational-two-pole source-front trace, and no replacement formula is imported.
See [the authors' paper](https://people.tamu.edu/~guermond/PUBLICATIONS/GKPT_WaterWaves_2022.pdf).

NEXT: one-sided transport and curvature at the eight newborn/unowned edges,
compatible joint force/impulse/time evolution and edge/flat/mixed transitions,
then native single-surface integration and actual motion/reference validation.
No Unreal build or capture is claimed for this offline-only increment. Last
ordinary South Fork remains 22.429181 FPS / p95 54.7266 ms, failing 30 FPS;
smooth wave faces and broad froth remain unaccepted. Colorado → Pacuare →
Futaleufu, Chilko/Zambezi/all-scene water, crew, normalization, retained
regressions and release remain open. Troublemaker stays within South Fork,
never as its own menu scenario.
