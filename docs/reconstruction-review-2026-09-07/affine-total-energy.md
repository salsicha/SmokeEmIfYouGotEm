# Completed source pullback and prescribed-boundary total energy

September23,2026. Supporting physics progress, not a playable water update.
South Fork and the complete ordered reconstruction/release queue remain open.

Follow-up: [original-source total-energy qualification](affine-total-energy-source.md)
now completes all11 supported original cases with independent branch gravity
checks and no repeated pressure solve. The controlled-only/source-replay-open
statements below describe this earlier checkpoint, not that completed follow-up.

## The source job actually completed

Original process6480/session50573 is terminal, exit0. The complete145,740,626-byte
report was written at17:18:24UTC. All11 supported original cases pass; unsupported
cases2/7 remain explicitly unsupported and retained. Rechecked every entry in
the635-file protected map and19-file implementation map: zero mismatches.
The [completion receipt](affine-total-energy/source-completion.json) binds the
complete local report SHA256 `3db5edcef9a413dffaf0c6028658e22188ca0b279ce7a381098c70be55dd443e`.
This supersedes earlier LIVE notes. There is no live scientific job or cook at
this inventory check. Do not restart this audit or reuse the old PID6480 profiling
wrapper; a future capture must use a freshly verified workload inventory.

This report qualifies the original saved pressure states and kinetic-energy
primitive derivatives, not the new total-energy module below. No unsupported
source was silently filled, no source equation re-solved just to repeat a pass,
and no captured XYZ, classification, collision or installed4950s flow changed.

## Total energy with the prescribed exterior trace

The existing reflecting-only total-energy wrapper intentionally rejects affine
pressure traces. The new `AffineFrontTotalEnergyVariation` supplies the missing
composition for the prescribed-boundary model: original two-pole kinetic energy
plus `g*integral(h*h/2 + (bed-datum)*h)` over each original moving-front owner.
It retains the curved-depth spatial moments, not footprint centroid times volume.

For physical momentum `p=Bv+q`, kinetic energy is `v.Bv/2-dual_constant`;
using `p.v/2` would omit the prescribed lift/constant contributions. Both
physical and canonical derivative coordinates remain available. Exterior-flux
work remains its own explicit term. Gravity adds the same potential derivative
in both coordinates, including bed slope/height and depth-weighted spatial
moments. The energy datum is fixed; changing it produces exactly the associated
mass and mass-rate work, not a new momentum force.

The constructor reuses qualified canonical/auxiliary states through the existing
exact equation checks, or performs the original solve when no state is supplied.
No alternative pressure poles, float clipping, positivity floor, residual force
or tolerance relaxation is introduced. Invalid bed/gravity and corrupted saved
states are rejected, including a1e-400 bed or velocity alteration.

## Validation and limits

The first test invocation failed collection because SciPy was absent from its
search path; the already installed task-local dependency was used for the next
run. That run passes66 tests. A subsequent expanded invocation named a nonexistent
audit test and ran zero tests; its failed XML remains. The corrected expanded
suite includes all new total-energy primitive checks, fresh-time geometry,
datum/shape/corruption checks, prior reflecting gravity/branch quadrature tests,
affine primitive derivatives and original source-reuse audit tests. All92 tests
PASS in59.15s, including23 new cases; [test/source hashes](affine-total-energy/tests.json)
retain both successful and failed invocations.

Independent complex-step checks rebuild both pressure poles and the potential
for every primitive in both coordinates at the unchanged1e-10 gate. Exact checks
retain all seven work contributions, including nonzero boundary-flux and spatial
work. Fresh geometry/momentum central differences independently check the total
time derivative. These are mathematical controls, not a source-wide total-energy
replay, nonlinear force, native GPU implementation or engine-motion acceptance.

Next couple this qualified total-energy derivative to a compatible conservative
transport/force law with explicit exterior work and front activation. The closed
periodic `rational_velocity_bracket_reference` changes transport relative to the
original finite-volume model and must not simply be spliced into its histories.
Interacting source fronts, natural/radiating pressure conditions, native cost
and full playable validation remain unresolved. Nonlinear normal gameplay stays
OFF. No map/material/engine rebuild or new FPS claim is made for this Python-only
change; the last normal26.484402FPS/p9547.2133ms still fails30FPS.
