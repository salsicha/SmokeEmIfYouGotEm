# Two-dimensional metric transport — September 14

The preceding turn made progress on a one-dimensional, positive, flat research
stage. This extension retains **both physical velocity components**, including
vortical currents, the same two poles, and the same physical/canonical momentum
map. It is still offline research: variable terrain, wet fronts, time evolution,
open boundaries and native/shared-surface integration remain unqualified.

## The tensor coupling cannot be copied from one dimension

Retain `G=D_h^T h^3 D_h`, `L=h+beta G`, `T=L^-1 h`, `R=I-T`, with vector
auxiliary velocity `w=T u`, vector difference `r=R u`, scalar `d=div(w)`, and
`c=h^3 d`. The flat continuum stationarity relation is
`h*r/beta=-grad(c)`.

In two dimensions the missing cross-mode operator is

```text
N z = div[c ((div z) I + (grad z)^T)]
S_cross = alpha (T^T N - N T)
```

Here `(grad z)_ij = partial_j z_i`. N is symmetric: integration by parts
gives the symmetric bilinear form
`-integral c [(div y)(div z) + sum_ij partial_j y_i partial_i z_j]`.
It annihilates constant vectors. Therefore the cross-mode commutator is skew
and its force preserves both total momentum components. In one dimension,
`N=2 d_x(c d_x)`, recovering the previous cross-coupling exactly.

For the continuum derivation, the auxiliary canonical momentum is
`m=-alpha*grad(c)`. Subtract the independent-mode skew transport from half the
metric derivative plus the Euler–Poincare advective/pressure force. The remaining
force is `alpha [N r - R^T N u]`, equal to the commutator above. Both
`(u dot grad)m` and `(grad u)^T m`, as well as `m div(u)`, are included.
Dropping the transposed-gradient contribution is not a full-dimensional model.

The implementation pairs each reconstructed directional derivative with its
actual transpose and face interpolation, rather than assuming a variable-depth
derivative is itself skew. The independently reconstructed physical momentum
flux includes **off-diagonal tensor faces** as well as the diagonal pressure,
metric derivative, acceleration and auxiliary transport faces. Its local
divergence is checked against `h*u_t+h_t*u` without resetting either value.

An explicit `longitudinal-only` comparison retains `2*grad(c*div(z))` in place of
N. This is a diagnostic, not an alternative accepted full-dimensional model.
The smooth refinement controls alone may not resolve its smaller missing term;
passing a coarse-grid convergence trend does not override the tensor derivation.

## Finer-grid pressure solve: fixed operator, better preconditioning

The initial 64x64 audit stopped because the existing patch-preconditioned
physical-momentum round trip failed its unchanged 1e-10 relative-to-state check.
It was not treated as an accepted measurement or resolved by lowering resolution,
raising the 40-CG iteration limit or relaxing the gate.

The new opt-in `spectral-flat` preconditioner inverts the **frozen constant-depth**
matrix at each Fourier frequency:

```text
k = (sin(theta_x), sin(theta_y))/dx
P = I + length * mean(h)^2 * k k^T
P^-1 r = r - length*mean(h)^2*k*(k dot r)/(1+length*mean(h)^2*|k|^2)
```

Every actual CG matrix action, factor derivative and true residual still uses
the original **variable-depth reconstructed operator**. The frozen-depth FFT is
only an SPD preconditioner, not substituted physics or a standalone pressure
answer. Constant and Nyquist null modes are retained. Nonflat beds or partial
dispersion are explicitly rejected. Original research APIs retain their previous
defaults; the new 2-D research entry point selects the flat preconditioner.

Tests compare the preconditioner with the exact constant-depth inverse, verify
positive/symmetric action, compare the final variable-depth 40-CG solution with
an independently assembled dense matrix, and show that the preconditioner alone
does **not** solve the variable-depth system. Small resolved stages agree with
the original patch-preconditioned stage. No native timing claim is made.

## Validation scope

The independent nonlinear reference uses the stationary dual kinetic density's
depth derivative and the full canonical velocity bracket:

```text
v_t = -grad(H_h) - curl(v) J(u), J(u)=(-u_y,u_x)
```

It does not reuse the new tensor stress. Both fixtures have nonzero canonical
vorticity and spatial variation in both velocity components. They are sampled
at 16x16, 32x32 and 64x64 on the same 16m x 16m domain; RMS rate errors do not
benefit from shrinking the physical domain. The original canonical-stress
control is compared independently, with identical sources and preconditioning.

All six final grid/profile cases pass energy, mass, both total momentum
components and local momentum-flux checks at 1e-10. Maximum absolute energy rate
is 7.11e-15, local flux error 1.93e-14, true pressure/auxiliary relative residual
1.78e-15, and physical-state round-trip error 1.78e-15.

| Seed | Full rate RMS, 16x16 | 32x32 | 64x64 | Refinement ratios |
| --- | ---: | ---: | ---: | ---: |
| 2310 | 0.00552858 | 0.00132190 | 0.00032671 | 4.182 / 4.046 |
| 2312 | 0.00550228 | 0.00131520 | 0.00032502 | 4.184 / 4.046 |

Canonical vorticity RMS spans 0.120–0.127, so these are not disguised potential-
flow controls. The incomplete tensor comparison has larger fine-grid errors
(0.00034317 and 0.00034770), but its ratios still exceed three on these grids;
**this particular trend gate alone does not reject that incomplete model**.
A separate 10x-velocity exploratory check at 16/32 cells likewise did not
isolate the tensor discrepancy. Neither comparison is promoted to a stronger
discrimination or acceptance claim than it supports.

The targeted tests also exercise irregular positive 2-D states, both-axis
reduction to the prior longitudinal stage, axis exchange, velocity reversal,
steady transverse shear, and an oblique linear wave's pressure, mass and
transverse null response. These are necessary controls, not a terrain or
finite-time acceptance claim.

The final targeted suite passes **32 tests** in 259.30 seconds: seven spectral
preconditioner checks, eleven full-velocity 2-D controls and all fourteen prior
longitudinal-stage regressions. This runtime includes slow research geometry
assembly and is not an engine performance measurement.

The retained original suites were rerun: **41 PASS / 12 FAIL**, exit 1. The
12 failures remain the eight old paired-stress nonlinear energy gates and four
legacy constant-velocity gates. The new optional preconditioner did not silently
redirect or waive those default-path tests.

Reproducible commands:

```text
python physics/scripts/audit_rational_metric_transport_2d.py --report FRESH_PATH
python -m pytest physics/tests/test_flat_spectral_pressure_preconditioner.py physics/tests/test_rational_metric_transport_2d.py physics/tests/test_rational_metric_transport_stage.py -q
```

Final source-locked audit: `tmp/two-pole-2d-metric-consistency-v2-20260914.json`,
SHA256 `c9c2ff5086f8f032ed92228cb1ff2d0c8d11e252a4bd2f6bb7cbcecc5e24de94`.
Exit 0 means the listed research checks passed; the full-qualification flag is
still false. The initial patch-preconditioned run terminated before producing
a complete v1 report and is not counted as a completed audit.
The final test reports are `tmp/two-pole-2d-final-controls-v1-20260914.xml` and
`tmp/two-pole-2d-retained-gates-v1-20260914.xml`.

All 464 protected scene/source/actor hashes were freshly checked unchanged.
There is no new Unreal capture, visual pass or FPS improvement. The latest
ordinary South Fork run remains below 30 FPS, and rapid shape/breaking/froth
remain visually unacceptable. Next required work is compatible exact-terrain
bed-force/energy coupling, then finite-time, wet-front/open-boundary and native
qualification. All later-river, crew, normalization and release work remains open.
