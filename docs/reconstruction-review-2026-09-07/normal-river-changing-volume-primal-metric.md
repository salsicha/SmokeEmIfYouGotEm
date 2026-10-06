# Changing-volume physical/canonical metric

September 14, 2026. This ports a required variable-volume term to the exact
source-pool geometry. It is a coefficient/direction calculation, **not** a
complete nonlinear force, time update or native water implementation.

## Differentiate the original map, including both volume factors

Use the same inverse factors derived algebraically from the original two
pressure poles: K=K0 I + sum(alpha Q (I+beta Q)^-1). No pole is refitted.
For physical momentum P, reference pool volume V, R=sqrt(V), canonical velocity
v=R^-1 K R^-1 P, and ell=V_dot/(2V):

```text
q = P/R
q_dot = P_dot/R - ell*q
(I + beta Q) z_dot = q_dot - beta Q_dot*z
v_dot = [K0*q_dot + sum(alpha*(Q_dot*z + Q*z_dot))]/R - ell*v
(V*v)_dot = V_dot*v + V*v_dot
```

Q_dot includes the exact local Gram derivative, both shared-face owners,
reflecting walls, oblique internal source faces, divergence denominators and
both velocity normalizations. Its unscaled action is evaluated directly; it
is not recovered by multiplying by a pole length and subsequently dividing.
Direct Q actions also avoid the near-constant-mode subtraction `(q-z)/beta`.
All inverse and derivative solves keep the original 40-CG / 2e-5 gates.

At fixed physical velocity u, P=V*u and P_dot=V_dot*u. Thus `(V*v)_dot` is
C_dot*u for C=R K R. Holding physical momentum fixed instead would give the
wrong term. This C is the physical-velocity inertia metric; it is distinct
from the dual matrix R S R used in the preceding linear-wave elimination.

## Independent local and energy-coordinate checks

For auxiliary w=z/R, form `(Pi,tau)=Gram*(D*w,w)`. The original identity

```text
V*v = K0*P + sum(alpha*(D^T*Pi + tau))
```

is differentiated independently into base momentum, stress divergence,
changing-divergence and terrain-metric terms. Their local sum must reproduce
the differentiated canonical momentum at 1e-10. Terrain-metric rate is a part
of this coordinate/metric derivative, not an already complete physical bed
force or acceleration. The full nonlinear auxiliary transport and terrain
work are still missing from the evolved river model.

The derivative of `P dot v / 2` is separately compared with the existing
reverse physical-energy gradient. At fixed u, half `u dot C_dot*u` must equal
the corresponding kinetic energy derivative. These are chain-rule identities;
they do not assert that an arbitrary prescribed direction conserves energy.

Thirteen tests cover independent perturbed maps/energies, inversion through
the original dual derivative, fixed-velocity versus fixed-momentum behavior,
zero directions, disconnected pools, nontrivial terrain terms, flat-bed null
reaction, complete metric-time self-adjointness, unscaled-operator range, and
audit scope/state preservation. The periodic moving-depth fixture is 3x4,
avoiding an all-Nyquist 2x2-only flat control.

## Original moving South Fork state

The actual audit retains the original physical momentum on all 258 source
pools. Its zero-sum volume direction and velocity direction are prescribed
verification inputs, **not computed river mass flux or acceleration**. No
original velocity is replaced by the artificial lake control.

All three fixed-topology probes pass the existing 1e-6 differential gates:
maximum canonical-rate error 7.32e-10; metric-time-force error per pool volume
6.73e-10. The dual inverse derivative returns the supplied physical momentum
rate within 6.28e-11 per pool volume. Local canonical-metric error is 1.78e-15;
energy-coordinate and fixed-velocity work errors are 7.11e-15.

Verification intervals are 1e-4, 5e-5 and 2.5e-5. The smallest probe has relative
total-energy derivative error 1.54e-7; subtracting total energies is already
roundoff-sensitive. This is not claimed to show monotone derivative-error
refinement. Both original inverse factors retain 40 iterations, with derivative
relative residuals at most 3.36e-16. Terrain-metric rate is nonzero (maximum
0.9351 for the prescribed direction); it is not inferred from a residual.

Report: `tmp/south-fork-primal-metric-direction-v1-20260914.json`, SHA256
`5d8e8f7f75b2b4c36937ab9a66c17ead371c3ba2da0c8fb6e43239a671935c89`.
All 45 source hashes match. Reproduce using the existing actual-source driver
with `--exact-pool-geometry --pool-primal-direction` and a fresh report path.

Focused suite: **301 PASS / 1 retained geometry FAIL**, 43.40s, recorded in
`tmp/subcell-primal-metric-suite-v2-20260914.xml`. Retained energy selection:
**25 PASS / 12 FAIL**, in `tmp/subcell-primal-metric-retained-v1-20260914.xml`.
No existing gates were relaxed or redirected. All 464 protected source,
scene, actor and prior runtime evidence hashes remain unchanged.

The actual drainage timestep comparison also completed; see the updated
[source-time refinement record](normal-river-source-time-refinement.md).
No owned numerical job remains running from these checks. Next is compatible
full nonlinear auxiliary advection/terrain work and evolving wet support, then
open boundaries and native/shared-surface integration. Playable terrain/water/
froth, 30 FPS, later rivers, crew, normalization and release remain unfinished.
