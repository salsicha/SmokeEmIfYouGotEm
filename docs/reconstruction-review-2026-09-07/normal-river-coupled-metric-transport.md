# Coupled two-pole metric transport — September 14

The preceding commit preserved a positive-periodic research stage, not a river
solver. This turn found and corrected its missing nonlinear auxiliary coupling.
The original independent-mode construction conserved energy and total momentum
but did **not** approach the intended continuum momentum rate under refinement.
It remains available only as an explicit negative control. Gameplay is unchanged.

## Why the additional coupling is necessary

Use the existing inverse physical kinetic metric, with the same two rational
poles and original reconstructed derivative D_h. For each positive inverse
factor alpha, beta, define

```text
G = D_h^T h^3 D_h
L = h + beta G
T = L^-1 h,  R = I-T
w = T u, r = R u
A_extra = sum alpha G T
A = K0 h + A_extra
```

The positive stationary kinetic density for each pole is
`alpha/2 * [h^3 (D_h w)^2 + h r^2/beta]`. The stage equation is

```text
h_t = -div(mean(h) mean(u))
A u_t + base_rhs + (A_extra)_t u/2 + S u = 0
base_rhs = div(K0 F_h mean(u) + g mean(h^2)/2) + K0 u h_t
```

The changing metric term is evaluated analytically at fixed physical u, including
the normalization, both pressure solves, and every reconstructed-factor tangent.
It is not a finite-difference derivative or global energy correction.

Transporting the two stationary modes separately gives a skew S, but that alone
does not reproduce their constrained nonlinear dynamics. The missing term is

```text
c = h^3 D_h w
M = D_h^T c D_h
S_cross = 2 alpha (M T - T^T M)
```

M is symmetric, so this commutator is skew and does no net kinetic-energy work.
Also T*1=1 and M*1=0 on a flat bed, preserving total momentum. No projection,
rescale, fitted coefficient, changed pole or looser pressure tolerance is used.
The original 40-iteration solves remain in place.

For an independent continuum derivation, write D=d/dx, `c=h^3 w_x`, and use
stationarity `h r/beta = -c_x`. The Euler–Poincare force for this pole is
`(A_extra)_t u + u m_x + 2 u_x m - h (L_h)_x`, where
`m=alpha*h*r/beta` and `L_h=alpha/2*(3h^2*w_x^2+r^2/beta)`.
Subtracting the half-metric term and the independent-mode skew transport leaves

```text
2 alpha [T^T d_x(c r_x) - R^T d_x(c w_x)]
```

Since `D^T=-D`, this is exactly `S_cross*u` in the continuum. It vanishes in the
standard SGN limit T=I, which is why a one-pole SGN limiting argument alone did
not expose the missing term for the project's rational response.

## Local physical momentum, not just a zero total

For the original reconstructed flat derivative,
`D_h^T c = -div(J(c))`, with face interpolation
`J(c)_i = other_i*c_i + own_i*c_(i+1)`.
The implementation independently forms the physical momentum face from:

- the paired base face;
- the extra acceleration metric face;
- half the complete fixed-u metric face derivative;
- the independent-mode and cross-coupled skew faces.

Pullbacks use `T^T y = y-beta G L^-1 y` and
`R^T y = beta G L^-1 y`. Their finite solve errors are retained, not silently
removed by replacing the calculated force with its conservative reconstruction.
The returned local residual compares `p_t=h*u_t+h_t*u` to the negative face
divergence. Each shared face contributes opposite amounts to its two owners.

## Actual results

All four original smooth flat profiles were run at 32, 64 and 128 cells, including
the eight required 64/128 states with identical source-state hashes. Across the
12 cases, coupled transport passes instantaneous energy, mass, total momentum
and independent local momentum-flux checks at the existing 1e-10 threshold.
Maximum absolute energy rate is 3.78e-15; maximum local flux error is 9.86e-14;
maximum pressure/auxiliary relative residual is 1.38e-14 (gate 2e-5).

The nonlinear rate oracle independently differentiates the stationary **dual**
kinetic density with respect to h at fixed canonical velocity and auxiliary
fields, then applies `v_t=-d_x(H_h)`. It does not reuse either candidate's stress
formula. It retains the original coordinate derivative and pressure solves.
This is a consistency control, not an exactly conservative discrete replacement.

| Seed | Independent modes, 128-cell RMS error | Coupled modes, 128-cell RMS error | Coupled refinement ratios, 32→64 / 64→128 |
| --- | ---: | ---: | ---: |
| 2200 | 0.01017020 | 0.00061617 | 4.023 / 4.005 |
| 2202 | 0.00928629 | 0.00035126 | 4.046 / 4.011 |
| 2204 | 0.00830419 | 0.00035662 | 4.010 / 4.003 |
| 2206 | 0.00814589 | 0.00039742 | 4.065 / 4.016 |

These are pointwise longitudinal momentum-rate RMS differences, **not** domain
integrals that artificially shrink with the one-cell transverse width. The
independent-mode fine-grid ratios stay near one (0.997–1.054), while the retained
canonical stress control independently approaches the potential control at
approximately second order. Conservation alone would have missed this defect.

The new targeted suite passes **14 tests**: original profiles and nonlinear
refinement; both-axis/sign constant velocity; original finite-kh pressure AND
mass response; velocity reversal and local face ownership; invalid scope and
incomplete audit rejection; and both-axis Galilean-boost refinement. The boost
momentum-rate defect decreases with ratios 3.913 and 3.977, while the mass-rate
transformation agrees to 1.71e-14. This is convergence, not exact discrete
Galilean invariance.

The **unchanged** prior required suite still reports **25 PASS / 12 FAIL**:
eight old paired-stress nonlinear energy failures and four legacy constant-u
failures. These were rerun, not skipped, weakened, or silently redirected to the
new implementation. No production solver default was changed.

## Reproducibility and limits

```text
python -m pytest physics/tests/test_rational_metric_transport_stage.py -q
python physics/scripts/audit_rational_metric_transport.py --report FRESH_PATH
python -m pytest physics/tests/test_paired_base_rational_stress.py physics/tests/test_conservative_rational_stress.py physics/tests/test_constant_velocity_mass_energy.py -q
```

Final audit `tmp/two-pole-metric-consistency-v2-20260914.json`:
SHA256 `2bbc63ca60a63672b728703cb7e9acf09911614dad7e3d8a3f056dd5071d619a`.
It locks all local script hashes before/after and exits 0 for its listed research
controls only; its full-qualification flag remains false. The earlier v1 report
records the rejected independent-mode implementation and exits 1.
Test reports: `tmp/two-pole-metric-controls-v2-20260914.xml` and
`tmp/two-pole-metric-retained-gates-v1-20260914.xml`.

All 464 protected scene/source/actor hashes were freshly checked unchanged.
No Unreal visual, performance or release acceptance is inferred from these
offline tests. The most recent ordinary South Fork profile remains 20.80 FPS /
p95 64.97 ms, below the requested 30 FPS target, and the actual motion review
still fails rapid shape, breaking and froth realism.

Next: extend the derived coupling to the full two-dimensional velocity system
and exact terrain, retaining local momentum/bed-force work; qualify finite-time,
wet-front, open-boundary and refinement behavior before native/shared-surface
integration. The stage explicitly rejects transverse and variable-bed states.
This is not sufficient for South Fork, let alone later rivers, crew or release.
