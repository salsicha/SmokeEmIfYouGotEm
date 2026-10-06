# Preserve small Rusanov return flows

September 14, 2026. Numerical correction in the research wet-pool path, not
qualified drying, native water delivery, visual realism or 30 FPS acceptance.

## Reproduced defect and correction

The signal bound is `s = max(|uL| + sqrt(g*hL), |uR| + sqrt(g*hR))`.
Previously, the donor kernel formed this as one float and then subtracted
velocity to obtain return flow. A positive wave contribution smaller than one
velocity ulp disappeared, although the resulting return flux was representable.

Eight independent Decimal-reference controls failed before correction: both
flow directions, flat/sloping faces, equal and adjacent floating-point
velocities, and different water depths. One flat-face case lost a return flux
of 1.5660459763365825e-117; the corresponding sloping-face case lost
7.830229881682913e-196. Near-ulp cases retained flow with roughly 0.8% error.

The donor kernel now selects the bound using a compensated comparison and
retains its advective and gravity-wave terms separately. Compensated sums
produce the original positive donor coefficients without subtracting from an
already-rounded combined speed. The same donors assemble mass and momentum
flux, including the original hydrostatic pressure. No flux is capped, added by
a floor, or recovered by changing the physical state. Numeric signal-speed
reporting remains a rounded projection; its two terms are also reported.

The controls compare complete mass/momentum flux to the independent formula
and repeat with exact source-face datums translated beyond float precision.
Both donor rates and flux values remain exactly translation-invariant in those
controls. Existing rotation, lake, energy, conservation and infinitesimal-rate
tests remain in force.

Two additional controls exposed genuine product underflow after this repair.
Positive return flux below float range now raises an explicit error, rather
than silently removing that donor. Actual zero-area dry faces remain valid.
This is a range safeguard, not a conservative drying model.

## Actual-source evidence

The first corrected exact-source South Fork run still passes 17 candidate
steps (0.34 s), then rejects four zero volumes at step 18; three have inflow.
It retains 420 regions. Maximum candidate speed is 5.806959739843258 m/s;
maximum per-step mass and momentum errors are 1.1368683772161603e-13 and
9.841016890277388e-13. These global budgets do not qualify tiny-region evolution.

Report: `tmp/south-fork-return-donor-history-v1-20260914.json`.
SHA-256: `cd16eabd555768969e755da4b5622ea07d6846171ab6e44cedde954866adb5fa`.
This report predates the explicit underflow guard; it must not be represented
as the final implementation's source-hash validation.

The final guarded run is terminal, exit 1:
`tmp/south-fork-return-donor-history-v2-20260914.json`, SHA-256
`1e0a491debe846102360cc1bf3d32fa87dbee397c85fa018fda756bd30d755b5`.
All 40 source hashes match. Its complete history is identical to v1, including
all budgets and rejection details; the new range guard does not trigger on
this run. Both original 40-iteration pressure controls pass. All 464 protected
source/capture/map/profile/actor hashes were rechecked unchanged.

The correction therefore rules out lost sub-ulp return flow as the cause of
this actual step-18 failure. Continuing the frozen linear mass drain is not a
substitute for conservative coupled wet/dry evolution and pressure-force timing.
Do not delete the three inflowing pools as isolated dry cells or promote this
research integrator into the normal South Fork game.

## Verification and delivery limits

Final focused suite: 235 passed, 1 retained original float storage/face
consistency failure. Retained energy suites: 25 passed, 12 existing failures.
No gate, tolerance, source geometry, physics timestep or render quality changed.
Local test records: `tmp/subcell-return-donor-suite-v2-20260914.xml` and
`tmp/subcell-return-donor-retained-20260914.xml`.

The ordinary entry point remains South Fork on `L_SouthForkAmerican_FullReach`;
Troublemaker remains a rapid, not a menu scenario. No native code or map changes
are part of this correction. The inspected existing normal-game capture still
has smooth green wave faces, broad merged froth and blocky rock flanks. No new
render or performance measurement is claimed. Full playable reconstruction,
30 FPS, later rivers, crew, normalization and release requirements remain open.
