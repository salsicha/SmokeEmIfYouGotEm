# Original point-birth geometry-time connection — September 15

The changing inertial metric alone is not the existing nonlinear equation's
complete geometry-time contribution. This increment derives and checks the
original geometric commutator and its pressure pullback alongside the earlier
half-metric force. It does **not** complete front transport, curvature, physical
impulses, time evolution, native integration or playable-water acceptance.
Both the source-activation and unequal-wet-support stage guards remain intact.

## Original terms and coupled limit

Use the prior point-birth path `V_new=r^2*e^3`, with exact source heights
`k_i*e`, fixed old volume and bounded fixed physical velocities. For each
original pole let `A=I+beta*Q_old`, `C=I+beta*D_new`,
`z=A^-1*R_old*u_old`, `v=B.T*z`, `x=C^-1*v`, and `a=-beta*x/r`.
Here `sqrt(e)*B` is the original normalized old/new pressure block and
`a=lim e*w_new` is the newborn auxiliary-velocity coefficient.

Recover the physical new/new divergence as `D_new,new=N/e`, retaining both
original volume roots and all coupled faces. Let `c` be the exact cross-Gram
coefficient `Gamma_D,u=e^4*c`. The original commutator formula gives:

```
j_old = lim (J_e*w)_old = -beta*R_old*B*x
j_new = lim (J_e*w)_new/e = -r*v + (c*(N*a)-N.T*(c dot a))/2
w_old dot j_old + a dot j_new = 0
```

The dot with `c` is per source. The last identity is a skew-work check, not a
reason to set either vector to zero. The new-source cross-Gram contribution
must survive. For the original pullback `T.T=R*(I+beta*Q)^-1/R`, define
`y=C^-1*(j_new/r)`. Its limits are:

```
pulled_old = R_old*A^-1*(j_old/R_old-beta*B*y)
pulled_new/e = r*y
connection = half the original M_e*u + sum(alpha*pulled)
```

The newborn normalized right-hand side is order `e^(-1/2)`, so deleting the
small old/new operator block before taking its product would lose an
order-one old force. `subcell_point_birth_connection.py` retains that product
through original positive factors, exact source coefficients and original
40-CG solves; there is no dense inverse, epsilon-water state, energy remainder,
force projection or new fitted pole. Residuals stay at 2e-5 and skew work at
absolute 1e-10. Independent finite-water probes alone create small positive
volumes; these are not accepted time steps or a minimum-depth treatment.

## Important cancellation, not a zero-force rule

In the unequal-stage planar two-source fixture, the old pressure pullback
cancels internally to roundoff. One newborn component cancels its half-metric
contribution, but other newborn components remain nonzero (maximum magnitude
0.0057931130969). Both effects are independently reproduced by positive-water
`geometric_commutator`, original pressure solves and `metric_time_force`.

The first test draft incorrectly demanded a nonzero old correction; the next
incorrectly demanded all newborn components cancel. These failed assertions
are retained in the v1 and focused-v2 reports. The implementation was not
altered to satisfy them. Final tests assert the actual partial cancellation
and nonzero coupled remainder, while keeping the independent vector/refinement
checks. Zero scalar skew work is not equivalent to zero force.

## Source-locked South Fork evidence

The simultaneous-birth audit now writes schema v4. Original block [12,8],
600-second snapshot: 16 old pools, 24 point births, four immediate new/new
edges, two paths with seven decreasing heights. All original energy, operator,
metric-force, work and source checks remain; the new check independently
assembles all commutator, pulled and combined force vectors.

Because some leading vectors cancel, errors are scaled by the magnitude of
their uncancelled original terms, not by roundoff in a zero result. This is
not componentwise relative accuracy. Full vectors and normalization scales
are retained. Each path's maximum term error must decrease by more than three
and end below 1%, without changing any prior gate.

| Path | First maximum scaled error | Final maximum scaled error |
| --- | ---: | ---: |
| Uniform stage | 0.742720% | 0.0116056% |
| Original receipt direction | 2.718477% | 0.0424849% |

Maximum analytic skew-work error: 1.302e-18. Maximum original finite skew work:
5.422e-19. Maximum original pullback residual: 2.153e-16. All diagnostic gates
pass; this does not measure energy through an evolved front.

Report: `tmp/south-fork-point-birth-connection-v1-20260915.json`, SHA256
`bf5b22fa0e968c30c85f1860649dd3b55173701cae8ceaca4fc8327b76e426c7`.
All 558 source/implementation hashes and 464 protected source/actor hashes
remain unchanged. Provenance remains 16 exposed-rock, four mixed
exposed/inferred and four inferred-flank receiving regions. The test-block
exterior is reflecting, not the natural open river; exact arithmetic does not
add measurement precision.

## Verification and remaining scope

Focused-v3: 84 PASS, including nine new connection cases. Final new-module
suite: 11 PASS, adding corrupted original pullback-residual rejection and
independent corrupted-vector detection. Tests retain unequal stages,
zero/nonzero bounded newborn velocity, stage reparameterization, zero old
motion, original finite vector refinements and the actual full-stage unequal
wet-support rejection. No feature is enabled by these diagnostic passes.

Full retained source/legacy-energy suite: **497 PASS / 13 unchanged FAIL**,
zero errors/skips, 117.97 seconds, terminal exit 1. All failure identities
match the preceding 486 PASS / 13 FAIL run: one legacy source-face rounding
consistency failure, eight paired-stress energy failures and four constant-
velocity energy failures. The existing JUnit record-property warning remains.
No gate was waived. Report: `tmp/point-birth-connection-full-suite-v1-20260915.xml`,
SHA256 `64e568491e09f6b7010a8a23f5283b97f938ac78d6975e3ae84bae9f51adf3ca`.
All owned audit/test jobs are terminal.

NEXT: complete one-sided front transport and curvature, compatible joint
forces/impulses and edge/flat/mixed transitions, verified finite-time and native
single-surface integration. This coefficient does not justify dropping the
remaining terms, assuming bounded newborn dynamics, or removing a guard.
No Unreal rebuild, fresh motion capture or FPS improvement is claimed for
offline-only changes. Last ordinary South Fork remains 22.429181 FPS / p95
54.7266 ms, failing 30 FPS; smooth faces and broad froth remain unaccepted.
Colorado → Pacuare → Futaleufu, Chilko/Zambezi/all-scene water, crew,
normalization, outstanding regressions and release remain open. Troublemaker
remains a rapid within South Fork, not a menu scenario.
