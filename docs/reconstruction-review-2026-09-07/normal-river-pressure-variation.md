# Pressure-energy variation on the original moving geometry

2026-09-18 UTC. A prerequisite for the nonlinear force law, not its completion.
Normal South Fork FullReach, terrain/collision, installed4950 water, render
material, timestep and quality settings remain unchanged. The nonlinear runtime
stays OFF. No visible improvement or30FPS acceptance is claimed.

## Reverse derivative, not an energy-residual correction

`subcell_front_pressure_variation.py` differentiates the existing physical
kinetic energy through both original poles and both volume-mass normalizations.
With `H_j=M+lambda_j*C`, `a_j=H_j^-1*M*v` and physical momentum `p=B*v`, at
fixed `p` the exact primitive derivatives are:

`E_M = -c*v*v/2 - sum_j w_j*(v*a_j - a_j*a_j/2)`;

`E_C = sum_j w_j*lambda_j*a_j*a_j^T/2`.

The implementation reverses `C=sum_i J_i^T*G_i*J_i` into local Gram and
divergence derivatives, then into the actual depth moments, bed slopes and
directed shared-face columns. It differentiates EACH owner's volume
denominator. A common face contributes through both adjacent owners, rather
than assigning two independently reconstructed columns. The source graph,
original pole constants and the supplied physical momentum are not altered.

For local depth moments `M1,M2,M3`, the Gram form is cubic in depth and retains
both bed-slope cross terms. Its derivatives are not replaced by a derivative
of mean depth. The exact result can contract arbitrary explicit primitive
directions; its actual-time contraction agrees with the preceding complete
metric-time work. It does not redistribute an energy residual into a force.

## Momentum coordinates must remain distinct

At fixed physical momentum, the momentum conjugate is canonical velocity
`v=B^-1*p`. At fixed canonical momentum `m=M*v`, it is layer velocity `p/M`.
The canonical geometry derivative is the negative of the physical one PLUS
the additional volume term from differentiating `v=m/M`:

`E_V|m = -E_V|p - sum_axes(p*v)/V`.

The canonical face-column, higher-depth-moment and bed-slope derivatives change
sign. Both coordinate forms are implemented explicitly. Feeding the canonical
momentum rate into the physical-coordinate derivative is a negative control,
not an interchangeable API use. Both correctly matched complete time-work
contractions agree exactly with the original physical energy rate.

No gravitational potential, conservative transport bracket, wetting rule,
open-boundary work or complete nonlinear force law is supplied by this module.
Those are required before native/playable integration. In particular, an
energy derivative alone does not repair the existing donor-mass and nonlinear
stress energy failures. Source provenance and inferred geometry remain distinct.

## Verification

Final new-module tests: **16 PASS**,10.33 seconds, zero errors/skips/failures.
Report `tmp/front-pressure-variation-tests-v4-20260918.xml`, SHA256
`b1f7923278f9887749a6b9fb9d20f82b56970e68640d3229b3f8cf185c695f13`.

- Independently rebuild the normalized two-pole energy from primitive values,
  without reading the implementation's stored divergence, Gram, kinetic matrix
  or derivative. Complex-step probes check EVERY physical- and canonical-
  momentum, depth-moment, bed-slope and face-column partial derivative.
- Independent real simultaneous perturbations converge at second order.
- Exact primitive, local Gram/divergence, matrix and full physical-time work
  agree, including the distinction between both momentum coordinates.
- Reordering the original source owners preserves derivatives and reverses the
  appropriate directed face gradient exactly.
- Positive sub-float mass/work and nonzero sub-float pressure-column derivatives
  survive. Fully dry sources have no fabricated velocity or wetting force;
  even a sub-float nonzero dry-face creation direction is explicitly rejected.
- Mismatched mass/geometry, a corrupted pole equation, wrong primitive shapes,
  an unknown momentum coordinate and a missing geometry-work term are checked.

The first9 tests passed. The expanded83-test focused suite passed before two
additional owner-order/sub-float controls were added. The next85-test run had
84 passes and one failed TEST ASSUMPTION: a uniform one-cell closed contour
has zero net divergence, hence exactly zero first pressure-column derivative.
That zero control is now retained, and an actual moving-front case tests the
nonzero sub-float derivative. No implementation equation or tolerance changed
to fix that test. Failed report remains
`tmp/front-pressure-variation-focused-v3-20260918.xml`.

Final broader regression: **784 PASS / 13 FAIL**,797 tests in63 modules,
zero errors/skips,261.05 seconds and one existing JUnit warning. All16 final
variation tests pass in this run. Serialized failure identities exactly match
the preceding suite: four constant-velocity energy, eight paired nonlinear
energy and one legacy storage/face consistency failure. No gate is waived.
Report `tmp/front-pressure-variation-full-suite-v1-20260918.xml`, SHA256
`3923c349baa6c12e046279ae4de7ed0039897e403468b879e249786e6b153bb7`.

## Original-source and runtime limits

The preceding original-source pressure-map audit completed without restart:
all11 supported cases pass, two unsupported records remain, and an independent
reload verifies the original records,628 hashes and serialized energy identities.
See [the completed metric report](normal-river-moving-pressure-metric.md).
The subsequent [original-case variation audit](original-front-pressure-variation.md)
reuses only its verified unknowns and rechecks the original equations. It is
still running; no all-source variation or native40-CG qualification is claimed.

The6600 and6650 hydraulic snapshots pass both full-state and dry-bank audits but are
not settled or installed. Physical breaking, convincing froth, raft/contact
and30FPS acceptance remain open. South Fork still precedes Colorado, Pacuare
and Futaleufu; Chilko/Zambezi, crew, normalization, regressions and release
remain in scope. Troublemaker stays a rapid within South Fork, not a menu item.
