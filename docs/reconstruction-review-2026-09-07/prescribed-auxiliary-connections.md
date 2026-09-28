# Auxiliary connections with prescribed pressure-flux coordinates

September28 UTC. Physics-reference component, not an enabled nonlinear solver,
physical exterior energy-flux law, playable improvement or river acceptance.
It extends the existing reflecting auxiliary operators to the prescribed
pressure trace used by the qualified affine energy model.

## What changed

`physics/scripts/subcell_prescribed_auxiliary_connections.py` keeps an explicit
coordinate for each exterior face's outward mass flux, q, alongside active
owner velocities, u. With C[row,face]=1/V[row], the same original pressure jet
has divergence D*u+C*q. No mean-depth replacement, new dry-owner velocity,
positivity floor, pressure pole or force from a global residual is introduced.
Defaults use the exact original fan's prescribed fluxes. Arbitrary coordinate
probes are mathematical variations, not a new admissibility/inflow policy.

Three existing skew connections are pulled back through this augmented jet:

- Shared-face factor exchange, using the original velocity-resolved h, h² and
  h³ face integrals, plus the original spatial factor connection.
- The spatial volume connection using the actual integral h*(u_adv.grad(h)),
  not the hydrostatic specialization grad(h)=-grad(bed).
- The physical-time connection at fixed u and q, with both D_t and
  C_t=-V_t/V². It does not silently incorporate a prescribed q_t trajectory.

The transpose supplies BOTH the interior action and flux-coordinate action.
Their work cancels exactly for self-pairing; distinct test states satisfy the
corresponding bilinear skew identity. With prescribed nonzero flux, the
interior work alone is generally nonzero. The explicit port term must not be
discarded just because the reflecting operator was work-neutral by itself.
Zero-flux interior actions reduce exactly to the existing three operators.

For the time derivative, the actual prescribed lift rate is
D_t*u+C_t*q+C*q_t. The last term is retained by the existing energy derivative;
it is not folded into the fixed-coordinate connection and counted twice.
Vector dimensions and nonfinite values fail closed rather than being truncated
by zip. Work-neutrality is checked after direct assembly; no action is fitted
or corrected from that residual.

## What this does NOT establish

Flux-coordinate work is not automatically the physical advective or pressure
energy flux. Shared-face transport here still lacks its advective exterior
closure. This component does not supply the full conservative mass/momentum
bracket, a time integrator, front interaction/activation, natural/radiating
pressure boundaries, breaking dissipation or a native implementation. The
previous original-fan versus dispersive-energy flux discrepancy is not erased.

The need to preserve mass and energy together is consistent with the
[SGN structure-preserving reference](https://arxiv.org/abs/2408.02665). This
augmented-coordinate construction is our explicit extension of the local
reference operators, not a claim to reproduce that paper's complete method.

## Verification

Thirteen new cases check exact reflecting reduction, nonzero and bilinear
port work, independent direct profile quadrature, fresh-time fixed-flux
geometry derivatives, winding, removed dry owners, positive subfloat water,
invalid dimensions and both original rational pressure-pole states. The new
tests plus existing auxiliary, profile-transport, prescribed-trace and affine
moving-pressure suites pass67/67, zero errors/failures/skips,120.827s. No
accuracy tolerance changed. This is not an original-source-wide replay or an
engine measurement.

The initial invocation collected no tests because pytest was not on the path.
Existing local dependencies were then used; no installation occurred. The
first collected run failed11 constructors because the exact Radical type does
not implement exponentiation. Replacing V**2 by V*V fixed that implementation
error; the next11-case run passed. Expanded validation added dimension and
pressure-pole checks and passed67 cases. Failed evidence is retained.

SHA256 evidence:

- New implementation:
  `fcba6bab59e9464169d04d5356ea2be80b915941e9c4e995ab97d998778e208e`.
- New test file:
  `f3b78d2cdcdcb0fe21cb326e02b0ba65f5407ef1cd193288591dee1aadd1ea04`.
- Failed `tmp/prescribed-auxiliary-connections-v1-tests-20260928.xml`:
  `fad6a9f996abd8265752822fea87e3a1fb29507af034a29655b27f3f26fb7923`.
- Focused passing `tmp/prescribed-auxiliary-connections-v2-tests-20260928.xml`:
  `e005fefb02cb2e16883889fc6cb9fed65a26e1312d7109af24b46c33adf8928f`.
- Expanded `tmp/prescribed-auxiliary-connections-v3-tests-20260928.xml`:
  `cae843ab28931a9c14162ab6fe5d98912b2438a8e8daf369815dd6683fdb21d3`.

Next derive the compatible advective exterior exchange and coupled momentum
law, including direct face/bed/boundary accounting; do not call these skew
identities a conservative evolving river. Nonlinear gameplay remains OFF.
No captured data, bed, geometry, installed fields or material changed.
Hydraulic owner33552/39708 remains live beyond1500s. Capture owner60320/4504
still waits for its terminal state and final audits; its frozen source hash is
unchanged. No duplicate cook, game benchmark or additional engine build ran.
