# Coupled point-birth metric-time force — September 15

The original pressure model now has a matrix-free vector coefficient for its
changing inertial metric at simultaneous point births. This replaces no force
in the playable solver. It is a required component, **not** a complete physical
front force, impulse, conservative time update, breaking mechanism, native
integration or visual acceptance. The actual bank activation guard stays on.

## Derivation and scope

Let the exact original source heights be `k_i*e`, with
`V_new_i=c_i*k_i^3*e^3`. Old volumes and all physical velocities are fixed.
For each original positive pressure pole, write `A=I+beta*Q_old`,
`C=I+beta*D_new`, `z=A^-1*R_old*u_old`, and `x=C^-1*B.T*z`.
The normalized old/new operator block is `sqrt(e)*B`; `D_new` retains the
coupled original new/new faces. The physical inertial metric is `M=R*K*R`.
The old-block Schur derivative and both volume roots give:

```
lim (M_e*u)_old = -sum(alpha*beta*R_old*A^-1*B*x)
lim (M_e*u)_new/e = 2*sqrt(c*k^3)*sum(alpha*x)
1/2*u_old.T*lim(M_e*u)_old = original kinetic energy path slope
```

`subcell_point_birth_metric_force.py` constructs `B*x` using the signed
original divergence columns, original positive source factors and their
transpose. It then solves the original old pressure system. The response can
reach old pools with no direct newborn face; applying a force only to the
donor or distributing a scalar energy deficit would miss this vector.

No epsilon-water state is constructed by the limit, no dry mass is inverted,
and no dense inverse, fitted dispersion, force remainder, energy projection
or eigenvalue repair is used. Both original poles, 40-CG / 2e-5 residual gate
and absolute 1e-10 work gate remain. Independent positive-water states are
test probes only. The existing fixed-support nonlinear stage needs metric
work together with auxiliary transport, curvature and boundary reactions;
this coefficient alone must not be installed as its full dynamics.

For the conditional parameterization `e=t^(1/3)`, these terms have leading
time powers `t^(-2/3)` on old pools and `t^(-1/3)` on newborn pools. They are
integrable coefficient singularities, not proof of a bounded-velocity
physical trajectory or a justified impulse law. Other front terms still
need derivation and joint verification. Edge, flat and mixed births are not
covered by this point-source formula.

## Original South Fork bank check

The existing source-locked simultaneous-birth audit now records schema v3.
For each of two seven-height paths it independently differentiates the
original positive-water metric with the established `metric_time_force`,
checking both the old force vector and newborn force divided by `e`.
Both vector errors must refine by more than three and end below 1%; all
existing energy, operator-column, bounded-base-work and source gates remain.

Retained original block [12,8] at 600 seconds: 16 old pools, 24 newly wet
original source regions and four immediate new/new connections. Final errors:

| Path | Old force max-norm relative error | Newborn coefficient max-norm relative error |
| --- | ---: | ---: |
| Uniform stage | 0.0406005% | 0.000126900% |
| Original nondispersive receipt direction | 0.116796% | 0.000566052% |

Each error decreases by approximately 64 across the seven probes. These are
vector max-norm checks, not relative guarantees on nearly zero components.
Full vectors are retained; manufactured coupled-source checks separately
exercise nonzero interactions. Maximum original direction solve residual is
3.565e-16; local canonical-momentum ledger error is 6.540e-19; physical energy
chain-rule error is 1.627e-19. Analytic work-identity error is at most 5.422e-20.
These numbers do not measure conservation of an evolved wetting front.

Report: `tmp/south-fork-point-metric-force-v1-20260915.json`, SHA256
`1f091026515265394da44b5ba3c1869a1e598141f895a93b183a5c41093003ed`.
All 557 source/implementation hashes and all 464 protected captured-source and
actor hashes match. Source provenance remains explicit: 16 exposed-rock,
four mixed exposed/inferred and four inferred-flank receiving regions.
Reflecting exterior block cuts are not the natural open river. Exact geometry
does not confer new measurement precision.

## Verification and remaining work

Focused suite: 56 PASS, including 12 new tests. Coverage includes unequal
coupled stages, zero/nonzero bounded newborn velocity, independent analytic
positive-water metric rates, an independent centered canonical-momentum
difference on three old pools, nonlocal old pressure response, symmetry,
linearity, stage reparameterization, zero old motion, unchanged state and
invalid/flat/stale-source rejection. Corrupted residuals and work fail;
corrupted vector coefficients remain visible to the independent audit.

The earlier focused v2 run had 55 PASS / one incorrect broad test expectation.
Its single-receipt manufactured fixture does not pass the pre-existing
all-column operator gate at the fixed seven heights, although its new force
checks pass. The corrected test explicitly retains that failed operator and
overall audit status; no gate, number of heights or tolerance was relaxed.
The actual 24-source bank audit passes all its diagnostic checks.

Full source/legacy-energy regression run: **486 PASS / 13 retained FAIL**,
zero errors/skips, 113.07 seconds, terminal exit 1. Failure identities exactly
match the preceding 474 PASS / 13 FAIL flat-birth run: one legacy source-face
rounding consistency failure, eight paired-stress energy failures and four
constant-velocity energy failures. No waiver or replacement gate was added.
The existing JUnit record-property compatibility warning is retained.
Report: `tmp/point-metric-force-full-suite-v1-20260915.xml`, SHA256
`a4a2aabe552ef7d5303e1bddb77528c6deac02bcc678d310cdcf502d8769b7dd`.
Focused report: `tmp/point-metric-force-focused-v3-20260915.xml`.
All owned audit/test jobs are terminal. No Unreal rebuild or new capture was
run because this increment changes only the offline model and audit; prior
playable evidence is not reclassified as fresh evidence.

NEXT: complete original front transport/curvature and compatible joint
forces/impulses, edge/flat/mixed transitions and verified finite time, then
native integration into the single playable surface. No visual or runtime
performance change is claimed. Last ordinary South Fork remains 22.429181 FPS
with p95 54.7266 ms, failing the 30 FPS target; broad froth and smooth wave
faces remain unaccepted. Colorado → Pacuare → Futaleufu, remaining Chilko and
Zambezi/all-scene water, crew, normalization, retained regressions and release
remain open. Troublemaker remains a South Fork rapid, not a menu scenario.
