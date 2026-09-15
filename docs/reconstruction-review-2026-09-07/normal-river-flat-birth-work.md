# Flat-source pressure work — September 15

This is an offline wet-front prerequisite, not a change to playable water or
an acceptance of breaking waves, froth, terrain, contact or performance.
Normal South Fork remains the menu scenario; Troublemaker remains a rapid.

## Why the point and edge limits cannot be reused

The original source geometry distinguishes point storage `V=c*e^3`, edge
storage `V=c*e^2`, and flat storage `V=A*e` as height `e` first becomes positive.
The flat case has no finite pressure-energy jump, but it does have a finite
height derivative. Both the old row's self-divergence change and bounded new
physical velocity contribute at that order. Ignoring either would give the
wrong work law even if the new principal pressure block tends to zero.

`physics/scripts/subcell_flat_birth_pressure.py` derives that limit from exact
source-face polynomials and the existing original two-pole old-state pressure
solutions. It does not construct finite epsilon water. The finite-water states
appear only in independent tests and are not used to estimate a production
force, fit the coefficients, or manufacture a front update.

For a flat minimum edge of width `w` adjoining strictly positive old water,
the original harmonic area is `2*w*e + O(e^2)`. Thus each old divergence row
gains both a normalized-new column proportional to `sqrt(e)` and an old-self
column proportional to `e`. Original face normals retain their signs,
including oblique within-parent source boundaries. Other dry support is not
converted into a wall. Existing old walls remain unchanged; the flat newborn's
own wall factors contribute only beyond the height-slope order.

## Original positive-metric derivation

Write the normalized pressure matrix blocks and momentum as

```
Q_oo = Q_old + e*Q1 + o(e)
Q_on = sqrt(e)*B + o(sqrt(e))
Q_nn = O(e)
q_new = sqrt(e)*r,  r = sqrt(A)*v
z = (I + beta*Q_old)^(-1) q_old
b = B.T*z
W = 0.5*z.T*Q1*z
```

The implementation accumulates `W` as the old divergence stress contracted
with its exact self-divergence variation. There is no dense inverse or repair.
For the same original positive coefficients `K0`, `alpha`, `beta`, the kinetic
height slope, canonical momentum derivative, and fixed-physical-momentum
volume derivative are

```
S = 0.5*K0*A*|v|^2 + sum alpha*(sqrt(A)*v.b + W - 0.5*beta*|b|^2)
C = K0*v + sum alpha*b/sqrt(A)
G = -0.5*K0*|v|^2 + sum alpha*(W - 0.5*beta*|b|^2)/A
S = A*(G + C.v)
```

The newborn auxiliary physical velocity tends to `v-beta*b/sqrt(A)` for each
pole. `C` is an energy derivative, not a measured raft-contact velocity.
The reported volume gradient is kinetic only; the existing positive-water
evaluator supplies gravity separately. The chain-rule work identity retains
the existing `1e-10` gate. Both original poles, the old 40-CG limit, `2e-5`
residual check and positive-energy contraction checks remain unchanged.

For the manufactured two-old-pool x fixture with nonuniform old momentum,
`A=0.125`, and new velocity `(0.37,-0.21)`, the analytic results are:

- Height slope: `-0.0015105011848315381`.
- Canonical velocity: `(0.5636714923948786,-0.21)`.
- Fixed-momentum kinetic volume gradient: `-0.2647424616647574`.
- Chain-rule identity error: `5.204170427930421e-18`.

Independent original positive-water evaluations give:

| New height | Kinetic energy difference / height | Canonical x velocity | Kinetic volume derivative |
| --- | --- | --- | --- |
| 0.001 | -0.001459545169280041 | 0.5624442823564636 | -0.2634733873449252 |
| 0.00025 | -0.0014977466535892603 | 0.5633644304661805 | -0.26442479435174354 |
| 0.0000625 | -0.001507311581327997 | 0.5635947107067806 | -0.26466301990961294 |

This negative slope is not permission to label energy loss as breaking
dissipation. No mass-transfer path, momentum impulse or time update is applied.

## Verification and limitations

The focused suite passes 23 tests. Seven geometries cover both Cartesian axes
and face orientations, an oblique source boundary within one parent, sloped
old terrain, and an exact-source datum offset of `2^35`. Energy, canonical
velocity, fixed-momentum volume derivative and both auxiliary responses
converge for zero and nonzero bounded new velocities. The tests explicitly
require nonzero old-self work and old/new coupling, so uniform-flow zero
stress cannot hide a missing pressure term. Full original operator columns
independently verify the old-self variation, cross block and vanishing new
principal block. Small dense matrices are test oracles only.

Zero old momentum retains the correct newborn base kinetic energy and velocity.
Stale state, owned source, invalid IDs, nonfinite/wrong-shaped velocity and
point/edge geometry are rejected rather than repaired. All finite positive
states retain original source geometry and old volume/momentum. No submerged
measurements or captured geometry are inferred from these manufactured cases.

The first 14 basic checks passed. Expanded coverage initially exposed a test
setup error: `state_from_stages` accepts absolute elevations, not offsets from
the artificial large datum. The fixture now constructs original relative
storage directly, preserving shallow offsets instead of rounding them through
an absolute float. That run's three setup failures remain recorded in
`tmp/flat-birth-pressure-v2-20260915.xml`. Corrected expanded checks passed,
then were strengthened with nonuniform old momentum; the final focused report
is `tmp/flat-birth-pressure-v4-20260915.xml` (23 PASS).

The first broader source/legacy-energy run finished with 474 PASS / 13 FAIL
in 161.52 seconds. After strengthening the new fixtures, the final full rerun
again finishes with **474 PASS / 13 retained FAIL**, zero errors/skips, one
existing pytest report-format warning, 111.13 seconds, terminal exit 1.
Its failing test identities match the earlier edge-birth suite exactly:
four constant-velocity energy cases, eight paired-stress energy cases, and
one legacy source-face/storage equality mismatch of `1.77635684e-15`.
No threshold, representation requirement or failure is waived.

Final evidence:

- Focused report `tmp/flat-birth-pressure-v4-20260915.xml`, SHA-256
  `42d0366e3dea851c5aa2935e940db2e7706e1f19eff40d71f0608760288855e9`.
- Full report `tmp/flat-birth-pressure-full-suite-v2-20260915.xml`, SHA-256
  `654b72dc1e60356f3737794cdd35c5b42aeb4725acba7b22e6381dc3bcada921`.
- All 464 protected source/actor hashes match the existing carrier-ground
  manifest. Generated reports remain ignored by Git. All owned jobs are terminal.

## Remaining dependency and acceptance

Point, edge and flat individual limits are now distinguished. Mixed/simultaneous
front work, compatible forces or impulses, conservative complete-front
transport, time stepping and native single-surface integration are still open.
The actual bank's previously audited 24 immediate receiving regions are point
births, not these manufactured flat fixtures; its activation rejection is not
resolved by this change. The finite-amplitude nonlinear path is not enabled in
ordinary play, and a linear height perturbation is still not an overturning
breaker. Repeating the rejected normal-only optics or transport-order trials
does not address that missing geometry.

No Unreal source, shader, material, geometry, collision or playback setting is
changed in this increment. No new engine motion or performance result is
claimed. The last ordinary run remains 13.420531 FPS / p95 89.9936 ms: FAIL
against 30 FPS / p95 33.333333 ms. Breaking/froth visual acceptance remains
open. Colorado, Pacuare, Futaleufu, Chilko/Zambezi water, crew, normalization,
retained regressions and release checks remain in the original queue.
