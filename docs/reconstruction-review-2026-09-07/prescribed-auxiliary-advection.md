# Signed exterior work in prescribed-fan auxiliary transport

September28 UTC. Physics-reference implementation, not a playable improvement
or completed open-boundary solver. The previous augmented connections kept
flux-coordinate work but only supplied a skew spatial operator. This change
adds its signed exterior symmetric part, without setting incoming work to zero.

## Construction and sign convention

`unreal/Plugins/SEIYGECore/python/scripts/subcell_prescribed_auxiliary_advection.py` retains the exact
original fan, source edges, bed gradient and prescribed pressure lift. Let E
map augmented owner-velocity/exterior-mass-flux coordinates to each boundary
jet `(D*u+C*q, ux, uy)`. On each ORIGINAL outward edge, integrate the same
velocity-resolved moments `mk = integral(h^k * (u_adv.n) ds)`, k=1,2,3.
The first moment must equal that face's original prescribed mass flux.

The factor channel uses the symmetric matrix

    B = [[m3,         -1.5*bx*m2, -1.5*by*m2],
         [-1.5*bx*m2, 3*bx*bx*m1, 3*bx*by*m1],
         [-1.5*by*m2, 3*bx*by*m1, 3*by*by*m1]].

Its half quadratic is the outward transport of the existing auxiliary factor
density `h*((h*d-1.5*grad(b).u)^2 + .75*(grad(b).u)^2)/2`. The separate
difference channel transports `h*|u|^2/2`. These are unscaled auxiliary
channels, NOT a new choice of their physical two-pole combination.

For either channel, the implemented spatial split is

    L = S + E^T B E / 2,
    v.L(u) + u.L(v) = sum_faces ((E*v).B.(E*u)),
    u.L(u) = sum_faces (outward auxiliary energy flux).

S is the existing shared-face/spatial skew connection. The transport RHS sign
is MINUS L. This convention is explicit in the returned receipt; adding L as
a positive RHS would reverse the intended outward-work sign.

Every exterior jet stress is assembled directly, then pulled back through the
existing divergence transpose and local velocity coordinates. Receipts retain
each original face, jet, stress and signed flux, plus separate interior and
prescribed-flux-coordinate work. No force is computed from an energy residual.
No absolute value, outflow-only clipping, volume averaging, dry-depth floor,
rounded unit normal or discarded positive subfloat support is introduced.

The transporting velocity remains the given fan's velocity field. Arbitrary
test coordinates vary the transported jet, NOT that advecting field. Incoming
work may be negative; this is not a positivity or energy-dissipation proof.
The fixed-coordinate time connection and prescribed q_t work are unchanged.

## Verification

The focused 12-case suite passed in54.14s. After adding an exact cross-state
boundary identity assertion, the new tests and existing prescribed connections,
front auxiliary/profile transport, prescribed trace and affine moving-pressure
suites passed79/79, zero errors/failures/skips,175.372s (session88517 exit0).
Independent numerical face quadrature evaluates
the actual pointwise factors, rather than reusing the implementation's moment
matrix. Other cases cover quadratic directional variations, exact reduction
to the existing interior skew contribution, both incoming/outgoing face work,
winding, hanging edges, exterior subdivision without splitting its owner,
dry-owner removal, positive water below float range, stationary transport,
invalid inputs and both original pressure-pole auxiliary states.

SHA256 evidence:

- Implementation: `f9a1a352bba686576b5f8207d5ccaf70317ec877fa452dcfdaf47a8edbabd120`.
- Tests: `abf8c364bf067799d266b1b8db50974c3df4a7de6251155629ec83b6450b76c0`.
- Focused `tmp/prescribed-auxiliary-advection-v1-tests-20260928.xml`:
  `5eaa117882b5f96a60e7b2b05b275bb7ae6668973fa8fd8439ac81a28b1a1366`.
- Expanded `tmp/prescribed-auxiliary-advection-v2-tests-20260928.xml`:
  `f1cf9f70560142c89df0c1e44eb549de1d3421acc81d0d676d9fc1866a18be0b`.

This is not an original-source-wide replay, evolved-flow test or engine result.

## What remains

This supplies an exterior Green-identity term for a frozen prescribed-fan
transport split. It does NOT prescribe incoming auxiliary states or supply
radiating pressure boundaries. The conservative coupled mass/momentum law,
physical pole weights and their full energy/source/pressure-work ledger,
front interactions/activation, slope junctions, timestep, breaking dissipation
and native implementation remain unfinished. Do not interpret the exact
boundary identity as a complete evolving-river energy balance, or substitute
the old nondispersive fan energy flux for the dispersive total energy.

No captured data, inferred bed, geometry, collision, installed fields, material,
engine source or binaries changed. Nonlinear gameplay stays OFF. Hydraulic
owner33552/39708 and queued isolated capture4504 remain the sole owners; all
five frozen capture input hashes were rechecked unchanged. No duplicate cook,
game timing or rebuild ran for this reference-only increment.

Next couple these directly assembled face/port terms to the physical momentum
law and validate the complete local ledger before any native integration.
The queued actual-game branch capture still determines the next runtime cost
change. Flat foam, weak breaking/rollers, hydraulic settling and South Fork's
reconstruction, collision, shoreline and rapid timing gates remain open.
