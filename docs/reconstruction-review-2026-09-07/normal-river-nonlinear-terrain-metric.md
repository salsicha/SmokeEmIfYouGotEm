# Nonlinear terrain metric transport: positive periodic research stage

This advances the missing nonlinear terrain coupling, not scene acceptance.
South Fork still needs exact-source changing wet support, open boundaries,
finite-time qualification, native integration, convincing shared-surface water
and measured 30 FPS. No later river, crew, or release requirement is closed.

## Original model and the missing geometric term

The original two-pole response and its derived inverse parameters are retained.
Write H=diag(h), D for the actual reconstructed divergence, B for its paired
bottom kinematic operator, F=H D-3B/2, and

    G = F^T H F + (3/4) B^T H B
    L_j = H + beta_j G
    T_j = L_j^-1 H
    w_j = T_j u, r_j = u-w_j
    C = K0 H + sum_j alpha_j G T_j.

The physical kinetic energy is u^T C u/2. All depth normalizations, reconstructed
coefficient rates, inverse solves and factor transposes are differentiated in
C_t u. The new stage evolves C u_t plus half C_t u and skew transport, not the
canonical momentum substituted for physical momentum.

For continuum interpretation define d=div(w), e=grad(b).w, a=h d-3e/2,
c=h^2 a and s=h(-3a/2+3e/4). The symmetric cross-mode operator is

    N z = div[c ((div z) I + (grad z)^T)] + s Hess(b) z.

The complete factor-time commutator is

    J = (F^T H F_t - F_t^T H F)/2
      + (3/8)(B^T H B_t - B_t^T H B).

F_t includes h_t D, h D_t and -3 B_t/2. In the smooth continuum, D_t=B_t=0
and J=(3/4)(D^T h h_t B-B^T h h_t D). It is generally nonzero on terrain.
In the actual discrete geometry the coefficient-rate terms are also retained.

Let A denote the skew scalar/vector operator
(h u . grad(z)+div(h u z))/2. Each inverse pole contributes

    alpha [T^T (F^T A Fw + (3/4) B^T A Bw + Jw)
           + (I-T)^T A r / beta + T^T N u - N w].

Each term is skew at fixed state; this proves zero kinetic work but is not a
standalone model-consistency proof. The terrain Hessian and J terms follow from
the stationary metric's Euler-Poincare form: use G w=-grad(c)+s grad(b), and its
fixed-u depth derivative 3h^2 d^2-6h d e+3e^2+|r|^2/beta. After extracting scalar
factor transport, the non-pullback terms are -Nw and the pullback terms Nu+Jw.
Independent turning-flow comparisons below are necessary checks on this algebra.

The tensor uses paired centered derivatives, so it is exactly self-adjoint.
F/B use the actual reconstructed geometry, including the cut and shared-bottom
coefficients. This is not bit-for-bit identical to the prior flat discrete
tensor stencil; it must retain the original continuum model and conservation.
The existing flat stage and production defaults are not redirected.

## Compatible gravity and independently assembled physical forces

Mass uses arithmetic depth and velocity means on the same faces. Gravity is
the exact transpose of this mass operator applied to g(h+b). Consequently its
work cancels potential-energy change and a nonflat lake at rest is stationary.

`terrain_metric_force_ledger.py` independently assembles local shared-face fluxes
and geometric sources from the original pressure-cut and bottom coefficients.
It does not define a bed force as the difference between final momentum rate
and a selected flux. For a pressure traction L(p,b)=-D^T p+B^T b, the component
face and local source are

    face_i = other_i aa_i p_i + own_i ab_i p_(i+1)
             + shared_b_i (b_(i+1)-b_i)
    source_i = (-aa_i+ab_(i-1)+local_p_i) p_i / dx + physical_b_i b_i.

Analytic differentiation gives the separate changing-coefficient ledger.
Factor/Gram/time/commutator ledgers follow from these paired operators. The
tensor ledger averages the cell tensor onto faces and includes its explicit
Hessian term as a geometric source. Inverse pullbacks use the identity
H L^-1 f = f-beta G L^-1 f. The physical force budget includes the acceleration
metric, half the changing metric and the full skew term. Flat terrain has zero
local bed source, not just zero total force. All local comparisons retain 1e-10.
This is a smooth-grid algebraic ledger, not acceptance of physical forces on
the exact captured-source wet/dry geometry.

## Independent model comparison and solver incident

The reference uses the original dual poles and canonical velocity curl, not
the candidate's skew/metric/force assembly. Its stationary depth potential is

    Phi = c0 |v|^2/2 + g(h+b)
          + sum_j weight_j [v.w_j-|w_j|^2/2
                            -(3/2) lambda_j (h div(w_j)-grad(b).w_j)^2]
    v_t = -grad(Phi) - curl(v) (-u_y,u_x).

The existing analytic original-dual coordinate derivative converts this to
physical momentum rate. Both horizontal components and nonzero canonical
vorticity are retained. Tests compare fixed 16 m square profiles on 16/32/64
grids, with separate no-commutator and no-Hessian controls. Those incomplete
controls conserve energy too; that is deliberately not enough to qualify them.

The first 64-grid patch-preconditioned comparison failed the unchanged physical
round-trip gate: max error 2.5563115846338746e-7. The run terminated; it did not
produce a completed report. No tolerance or iteration limit was relaxed.

An opt-in `spectral-frozen-depth` preconditioner uses the SPD constant-depth,
zero-slope reference inverse. Its Fourier eigenvalues are 1 and
1/(1+lambda h0^2 |k|^2), hence positive even when the actual bed is nonflat.
Every CG action and true residual still uses the complete original terrain
matrix, with the same 40 iterations. The old `spectral-flat` rejects nonflat
terrain as before. Small dense controls check symmetry, positive definiteness,
the original matrix solve, unchanged matrix coefficients, and agreement with
the independent patch preconditioner. This is research, not a native cost claim.

## Evidence status

Completed report: `tmp/terrain-metric-three-grid-v2-20260914.json`, SHA256
`42ecdcf3dc549737a820adc9a725963760fb60d15d4b0465b65b7b89ab7baee0`.
All 523 recorded implementation hashes match the completed worktree. Two
independent fixed profiles each completed all three grids. The 16 m domain,
original physical input, original poles, 40-CG and 1e-10 budget/round-trip gates
were retained. This report records measurements; exit zero alone is not a
model/scene acceptance gate.

| Seed | Grid | Full vs independent model RMS | Without J | Without bed Hessian |
| --- | --- | --- | --- | --- |
| 2401 | 16 | 0.00552187724 | 0.00543612313 | 0.00534513266 |
| 2401 | 32 | 0.00135741577 | 0.00241510312 | 0.00125520156 |
| 2401 | 64 | 0.000338246859 | 0.00231540779 | 0.000667296921 |
| 2403 | 16 | 0.00561180880 | 0.00576258766 | 0.00548625847 |
| 2403 | 32 | 0.00137676021 | 0.00232627294 | 0.00130294259 |
| 2403 | 64 | 0.000342929560 | 0.00201906884 | 0.000605521085 |

Full-model successive error ratios are 4.06793/4.01309 and 4.07610/4.01470:
second-order consistency on these profiles. Both incomplete controls also
conserve energy, but retain distinct nonvanishing force contributions and fail
the full model's refinement trend. Coarse-grid closeness alone would select the
wrong formulation. Canonical vorticity RMS is 0.1211-0.1286, not potential flow.
This is consistency evidence, not a proof for arbitrary terrain or wet support.

Across the six full profiles, maximum local physical-momentum ledger error is
4.66e-14, metric-time ledger 8.89e-16 and skew ledger 5.69e-16. Total momentum
rate equals independently assembled bed force within 2.4e-14. The largest
energy-rate magnitude across all variants is 8.44e-15. The 64-grid physical
round-trip is now <=2.00e-15, maximum reported solve residual <=2.22e-15, with
the original 40-CG limit. No finite time step has been qualified by these rates.

Completed tests (no waivers):

- `tmp/terrain-metric-unit-v5-20260914.xml`: **23 PASS**. Factor/time transpose
  and finite differences; tensor/commutator adjoints; local mass/energy/physical
  force; lake rest; axes/reversal/datum; flat bed null; dense preconditioner
  controls; original oblique two-pole wave response/transverse null; independent
  8/16/32 turning-flow refinement.
- `tmp/terrain-metric-prior-regression-v1-20260914.xml`: **55 PASS**, existing
  patch/flat-spectral pressure, original primal/dual/directional energy and
  1-D/full 2-D flat transport controls. No existing default was redirected.
- `tmp/terrain-metric-subcell-regression-v1-20260914.xml`: **301 PASS, 1 FAIL**,
  retained original source geometry discrepancy 1.77635684e-15; no fragment
  deletion or relaxed geometry comparison.
- `tmp/terrain-metric-retained-v1-20260914.xml`: **25 PASS, 12 FAIL**, unchanged
  old paired-stress/constant-velocity energy failures, not marked xfail.

All jobs above terminated. Aggregate selected coverage is **404 PASS, 13 FAIL**.
All 464 protected source/scene/capture/map/actor hashes were rechecked unchanged.

No native code, maps, assets, measured terrain, reference videos, collision or
performance evidence changed. No gameplay or full nonlinear/wet/dry/history
acceptance flag is set by this candidate.

## Next integration constraint

The actual-source pool operator uses an integrated 3x3 Gram form acting on
(D u,u_x,u_y), not a single sampled depth and bed slope. Its depth powers,
mixed depth/slope moments and slope covariance must not be replaced with a
mean-depth version of the smooth stencil above. The already verified pool
metric-time derivative supplies C_t u, including original volume factors,
changing face divergence, local stress and terrain terms. The next step is
the corresponding full nonlinear transport/connection and tensor work on
those original source moments and oblique faces, with explicit boundary forces.
Then couple it to conservative wet/dry events and finite-time/open-boundary
controls before native/shared-surface integration. The smooth stage supplies
an independent model limit for that work; it is not a replacement river grid.
