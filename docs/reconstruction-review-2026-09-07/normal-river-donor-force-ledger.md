# Donor exchange and direct source-force assembly

September 14, 2026. **Two instability mechanisms corrected; finite-time and
gameplay acceptance remain failed.**

The preceding history failed after tiny-region velocities grew despite global
energy decreasing. New local budgets distinguish the physical face contributions
from matrix-subtraction roundoff. The normal native solver, scenario, captured
terrain, water state, render quality and performance settings are unchanged.

## Negative exchange was a real force, not just conditioning

The unchanged paired-flux history reproduces the failure at parent 159 / source
600739. At step 11 its old volume is 1.2761518e-15 cubic metres, and its velocity
changes from approximately (-0.965, -2.029) to (-138.283, -75.822) m/s.

Its explicit remainder is (-2.9341793e-10, -1.5767370e-10). Of this, negative
velocity exchange contributes (-2.9332560e-10, -1.5762306e-10); pressure is only
(-9.4774e-14, -4.0845e-14), bed force is smaller still, and wall/dry-front terms
are zero. The normalized solve diagonal is about 7530, so this particular
acceleration cannot be attributed merely to an almost singular matrix.

Report: `tmp/south-fork-local-front-budget-v2-20260914.json`, exit 1.
SHA256: `527890fc246a151b57510c6df883fbadcd56879f041cb70707f9834b59185f45`.

The pressure-secant central flux can have negative velocity exchange near a
dry face. Its global instantaneous energy pairing does not give a local
invariant-domain or finite-step velocity guarantee. The original path remains
available as a comparison; its failure is not waived.

## Nonnegative donor alternative for the base component

The opt-in `coupled-donor` history uses the existing section-integrated Rusanov
nondispersive base flux, with the original linear-bed area and pressure moments.
For normal velocities uL/uR, wet face areas AL/AR and original signal bound s,
the two donor volume rates are

`L = (s + uL) AL / 2`, `R = (s - uR) AR / 2`.

Both are nonnegative. Mass flux is L-R; momentum flux is L*uL_vector minus
R*uR_vector plus the hydrostatic pressure vector. Its net-donor decomposition
therefore has velocity-exchange coefficient min(L,R), never a negative
coefficient. Both global XY momentum components are retained on oblique edges.

One-sided unowned-source activation still uses the existing dry-bed Riemann
front. There is no added dry volume, merging of disconnected water, velocity
cap, or reduced timestep. Tests cover a dry receiving face, coefficient
decomposition, rotation, exact-terrain lake balance, closed mass/momentum
budgets, and dissipative base-energy work on moving fully wet fixtures.

This changes the nondispersive base flux in the **explicitly selected research
candidate**. It is not the complete rational model and is not a substitute for
the required auxiliary transport, exact-terrain pressure/bed-force work or
nonbreaking energy requirements. Gameplay and the default audit scheme are
not switched to it. Finite base and full original-pole energy checks remain.

## A second failure: recovering small forces by subtraction

The first donor run removed negative exchange but still blew up later. At step
16 a region with only 3.1851e-167 cubic metres received a computed explicit
remainder of -8.2718e-24 in X. Direct face/bed contributions were around 1e-166.
The much larger value was rounding residue from subtracting the donor and
exchange matrix actions from the already assembled total momentum rate.

That residue is negligible in a global force norm but enormous per unit of
such a small water volume. Global energy decreased through step 15 while local
velocity had already reached about 1.03e52 m/s. Step 16 finally failed the
unchanged energy gate. None of these candidate budget passes is accepted
physical evolution.

Report: `tmp/south-fork-donor-front-history-v1-20260914.json`, exit 1.
SHA256: `b6f1ac6667a00b9deeacaa0f45df6226733e14eb50566daf992bc53367993d13`.

The correction assembles the explicit remainder directly from original face
pressure, bed force, wall force, any negative exchange, and one-sided front
force. Receiving source regions carry an equal/opposite direct force record.
Compensated summation combines these components. No velocity, depth, energy or
global total is corrected afterward. The direct ledger must reproduce the
original assembled momentum rates within the unchanged 1e-10 check.

A regression retains a force of order 1e-90 beside much larger transport terms,
and another deliberately corrupts a force record and requires rejection.
The dry-front Riemann branches also now integrate nonadvective momentum
directly: upstream pressure is g*h^2/2, and fan force is mass_flux*(c-u_normal/2).
This retains a 4.905e-200 pressure contribution that subtraction from the
advective momentum rounds to zero. Independent branch quadrature and rotation
checks cover the additional force record.
The coupled solve still includes conservative implicit positive exchange on
new velocities/new volumes; pressure and other remainder terms remain explicit.

## Final actual history remains incomplete

Report: `tmp/south-fork-donor-front-history-v3-20260914.json`, exit 1.
SHA256: `5c34fe6b545ab83b1e01de827307db342035bc824d32ec4a8e1eb7cae02aa62d`.
All 35 report source hashes were rechecked against the final code with no
mismatch. The report starts from the same original 600-second atlas and terrain.

The requested 20 fixed 20 ms steps still do not complete. Seventeen candidate
steps pass the finite budgets, reaching 0.34 seconds and 420 regions. The
catastrophic velocity growth above disappears: maximum speed is about 5.30 at
step 1 and 4.01 at step 17. A newly activated region briefly reaches 10.40 m/s
at step 14; its force/time coupling is not physically qualified by this test.

Maximum per-step mass error is 1.1369e-13; momentum boundary/bed balance error
is 1.1564e-12. Base and original full energy decrease across those candidates.
These are component budgets, not full nonlinear model or visual acceptance.

Step 18 rejects because the coupled volume solve is not all-positive/finite.
The previous step's minimum volume is 4.0498e-254 cubic metres. This is consistent
with the backward-Euler drying tail reaching the represented range limit, but
the report does not separately classify its zero/nonfinite entries. An
independent two-region test reproduces an exact positive backward-Euler result
near 5e-339, below float64's range, and verifies rejection without silently
deleting water. A global mass tolerance alone would miss that deletion.

Do not shrink the timestep, discard tiny regions, or call the first 17 steps a
qualified history. Next derive conservative drying/extinction events and
compatible force timing, and finish the full rational model, pressure/bed
coupling, open boundaries and space/time refinement before native promotion.

## Geometry endpoint fix and an unwaived representation gap

Re-interpolating an existing source endpoint as z0+(z1-z0) can move it by one
ulp. Shared-subsegment interpolation now preserves the endpoint exactly. The
new independent 64-segment control first failed, then passed without relaxing
its exact equality requirement.

A separate exact comparison still finds independently clipped storage and
canonical source-face coordinates differing by up to 1.7764e-15. The actual
force audit found such discrepancies in six regions, but not the failing
negative-exchange region; their largest gap/stage ratio was about 2.37e-13.
They were not the demonstrated cause of the original force explosion.

An attempted exact rational full-cell clip exposed positive sub-ulp fragments
that collapse in the current float-vertex storage API. It was not retained:
dropping those fragments or weakening the existing affine-source test is not
an acceptable geometry fix. The new storage/face consistency test remains a
real failing gate. A representation that preserves such fragments and consistent
relative heights is still required; no whole-geometry completion is claimed.

## Verification and remaining scope

Final focused suite: **173 passed, 1 failed** in 14.09 seconds, exit 1.
The remaining failure is the exact storage/face consistency requirement.
Report: `tmp/subcell-donor-source-tests-v4-20260914.xml`.

Retained three-file original energy selection: **25 passed, 12 failed** in
7.59 seconds, exit 1. The eight nonlinear and four legacy constant-velocity
failures remain unwaived. Report:
`tmp/subcell-donor-retained-gates-v1-20260914.xml`.

All 464 protected source/capture/map/profile/actor hashes remain unchanged.
Measured and inferred terrain provenance stays distinct. Generated reports
remain ignored local evidence. Reproduce the final actual failed run using a
new report filename and the locally installed NumPy dependencies:

```powershell
python -B physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/donor-history-new-run.json --pool-history-steps 20 --pool-history-scheme coupled-donor
```

South Fork breaking/froth/shared playable surface and 30 FPS validation are
still open. Colorado, Pacuare, Futaleufu, Chilko/Zambezi reviews, crew realism,
fit and animation, normalization, outstanding regressions and release checks
remain in the full goal. Troublemaker is a rapid within South Fork, not a menu
scenario. No native visual or FPS gain is claimed; full goal active.
