# Same-front hydrostatic energy transfer — not playable acceptance

September17,2026. The prior common side-front mass/momentum flux lacked its
corresponding energy transfer. This adds that instantaneous flux, not a coupled
state update or a fix for the existing nonlinear pressure instability.

## Physical definition and bounded integration

Use the SAME homogeneous zero-normal wet/dry rarefaction as
[the preceding side-front flux](normal-river-inlet-lateral-flux.md): interface
depth`h*=4h/9`, normal velocity`un*=2sqrt(g*h)/3`, unchanged tangential velocity`u`.
The dry-state rarefaction is described by the
[Clawpack Riemann book](https://www.clawpack.org/riemann_book/html/Shallow_water.html#Dry-initial-states).
The shallow-water mechanical energy and flux with fixed bed appear in
[Lampert and Ranocha, equations5–6](https://link.springer.com/article/10.1007/s44207-025-00006-3).
Only those shallow-water identities are used here, not that paper's different
dispersive model or its time-integrator qualification.

Our substitution of this interface state gives energy transfer per unit density
`q*(|u|²/2 + 2g*h/3 + g*(bed-datum))`. It includes pressure work; merely carrying
the upstream kinetic/potential energy with mass would be a different flux.
On the original ray`X=A+u*(R³-r³)`, the supplied affine bed is
`bA+grad(b).u*(R³-r³)`. With`Mp=integral(q*r^p dl)`, its primitive is
`16k/[9(2p+9)]*sqrt(g*k*|u|²*r^(2p+9))`. Combining powers0,1,3 gives the energy
flux without rounded source vertices or a guessed source crossing.

Every source gradient must agree exactly with its original polygon. Radical
and unresolved-crossing intervals enclose the signed result. The width gate is
relative to the sum of absolute full-ray moment contributions, explicitly NOT
relative accuracy of a possibly cancelling net energy flux. No depth/time floor,
erased sliver, repaired total or relocated water. Reference-elevation shifts
carry the expected`g*C*mass` term; shifting geometry and energy datum together
leaves the result exact. Wet debit/dry credit are correlated opposite bounds
of ONE flux, not two independent forces or a declaration of ownership.

## Tests and actual source

Focused final suite:66 PASS,4.42s. Includes independent physical-distance
quadrature of the interface energy+pressure expression, an independent integral
over the initially dry half of a centered fan, tangential velocity, signed energy,
datum shifts, rotated/wound/source-partitioned geometry, shared-front queries,
positive sub-float energy and explicit unresolved-budget rejection.
The homogeneous1D fan control is not a finite-time2D sloping-bed solution.
JUnit`tmp/inlet-lateral-energy-focused-v2-20260917.xml`, SHA256
`0deb7504c3cc0c130000e98d0e4396eb500f3cbdb2b96c39329cb34ffc07af30`.

Actual unchanged South Fork source-curvature report, registered terrain and
600s atlas, block(12,8):10 represented conditional streams,17 routed pieces;
all11 original receiving sources queried, including the sub-float stream.
Two receding/fan records remain unsupported.28 energy queries total;11 prove
positive energy transfer. Queries overlap ownership and MUST NOT be summed as
independent front transfers. Maximum scaled enclosure width1.521633e-243 is
arithmetic precision, not additional surveyed accuracy.

All original piece fields and mass/momentum flux reports are unchanged.
All612 recorded source/implementation hashes rechecked; original water unchanged.
Actual report`tmp/south-fork-inlet-lateral-energy-v2-20260917.json`, SHA256
`92d6d6522443f320cb09c3ec3ae92fd01e85f1edce2a3115f1be8633003b45a2`.

The first actual report hit Python's4300-digit decimal conversion guard on an
exact energy width scale. Its partial v1 file is retained as INCOMPLETE, not
passing evidence. Exact rational JSON now uses existing decimal strings when
representable and a tagged hexadecimal numerator/denominator otherwise. The
process-wide safeguard stays enabled. All bits and signs survive round trips;
invalid/unknown encodings fail. Final report declares its encoding and contains
one tagged field. Complete serialization is validated before opening the fresh
report, preventing this error from producing a new partial document.

The first broad regression completes639 PASS/13 FAIL,144.27s. Final
serialization-inclusive run completes654 PASS/13 FAIL,142.98s(142.952 JUnit),
667 total, zero errors/skips and one existing warning. All thirteen failure
identities match the preceding suite: four constant-velocity energy, eight
nonlinear rational energy and one original storage/face representation gate.
No threshold, skip or default physical model changed. JUnit:
`tmp/inlet-lateral-energy-full-suite-v2-20260917.xml`, SHA256
`653c65aad288b2130b42012f2a27926f640463377865bdde7d96744c75b537e5`.
One earlier launch correctly stopped before collection
on an unexpected class-qualified JUnit name; the corrected module mapping
retains class-based tests, verifies every path and adds the new modules.

## Hydraulic continuation and unclosed work

Same exact cook PID17516/start2026-09-17T12:52:03.0749210Z remains directly
verified LIVE. Complete4000s/local8000 passes state/conservation and all86,720
exactly dry artificial-bank cells. Maximum depth3.967027076m, speed5.345181854m/s,
volume2,895,098.356123m3, maximum step residual1.521822357e-8m3. Outflow92.421241620
versus inflow45.306954547m3/s: NOT settled or promoted. Next4050/local9000 needs
its marker and BOTH audits. h SHA256:
`2eaca702b4e353f80e3c748faf1d1bf3efda65861521c99ba5e60e2afb999991`.
Reports`tmp/control-ablation-4000s-{state,banks}-v1-20260917.json`.

Next derive single front ownership and evolving donor/receiver depth, momentum
and energy consistently with this flux, actual bed/curvature forces, dispersive
pressure work and branch transitions. Do not simply add it to the old
distributional pressure residual or claim conservation from opposite report
bounds. Finite-time2D fronts, all thirteen existing failures and native/runtime
integration remain unqualified.

No gameplay DLL, material, terrain or solver is installed/changed. Installed
gameplay/water-detail/material hashes match the preceding review. No new engine
motion or reference-video review, and no new FPS claim: last installed25.907729FPS,
p9544.7123ms still FAIL30. South Fork single-surface breaking/froth and consistent
terrain/boulder/collision/flow acceptance remain OPEN, followed by Colorado ->
Pacuare -> Futaleufu, Chilko/Zambezi/all-scene water, crew, normalization,
regressions and release. Troublemaker remains a rapid, never a scenario/menu item.
