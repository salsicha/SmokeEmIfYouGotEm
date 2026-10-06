# Temporal branch jumps: independent diagnosis and continuous mass candidate

September 14, 2026. Previous turn: PROGRESS (EP mass reconstruction and positive
RK2 reference exposed incomplete temporal convergence). This turn diagnoses
that failure on the SAME trajectories and adds a continuous mass candidate.
No native/gameplay, terrain, material, captured-source or original-history edits.
Full goal and 30 FPS/p95 33.333 ms remain open; physics120Hz/solver1.6ms unchanged.

## Actual trajectory diagnosis, not a replacement test

`audit_positive_rational_branch_crossings.py` replays all eight original
synthetic 64-cell smooth states for the same 16 steps of 0.0005 s. It labels
the original pressure MC depth/free-surface branches with rational arithmetic.
Where endpoint labels differ, it bisects the linear state segment and measures
both sides at relative distances 1e-3, 1e-4 and 1e-5. These are diagnostic
distances, not smaller replacements for an existing acceptance probe. Reported
crossing times are interpolated segment times, NOT exact trajectory event times.

Final trace: `tmp/south-fork-positive-rational-branch-crossings-v2-20260914.json`.
All eight final endpoint hashes exactly match the original finest evolution
report. There are 29 branch-change records, including paired depth/surface
changes at the same crossing; they are not 29 independent physical events.
The trace does not claim to detect switches that occur and reverse wholly
inside one step, nor all possible hydrostatic or EP-selector events.

The original fixture defines even seeds on a flat bed and odd seeds on a
sinusoidal bed. The four odd/variable-bed cases show persistent energy-gradient
and canonical-rate jumps. For example:

| Seed | Smallest-probe depth-gradient jump | Canonical-rate jump |
| --- | --- | --- |
| 2201 | 0.006290692 | 0.012594825 |
| 2203, surface at cell53 | 0.007147528 | 0.014307428 |
| 2207, surface at cell3 | 0.000771950 | 0.001542885 |

At seed2201, the canonical state gap falls from 3.1269e-6 to 3.1269e-8 while
the rate jump stays near0.0126. The mass-rate gap instead shrinks by100x.
This separates the pressure-gradient defect from mass transport in that case.

For EACH recorded crossing, the largest gradient-jump component was verified
using the independent `PressureGeometryRate`/dual-energy directional evaluator
on both sides. Maximum disagreement with the reverse gradient is7.105428e-15.
Both original poles and40-CG gates remain. Thus these jumps are not an artifact
of the reverse implementation or its actual-direction work check. A work-free
instantaneous stage does not by itself give a regular time-evolution vector field.

## A second discontinuity in the EP mass reconstruction

The EP transport itself jumps at some crossings. Seed2207's layer-velocity
gap is only1.729046e-8, but its retained-face jump is0.000677534, EP surface-slope
jump0.001441235, and mass-rate jump0.005834221. Flat-bed seed2206 also has an
EP mass-rate jump up to0.000399662. Pressure and transport issues must not be
conflated or fixed by merely swapping the pressure limiter to the same EP rule.

`test_ep_transport_continuity.py` gives an exact, independent counterexample
to the EP slope's hard wide-extremum switch. Its five represented values are

    [1, 1+t, 9/8+t, 3+t, 6+t].

As t approaches zero from above, the center slope is1/4. From below it approaches
15/64, leaving a1/64 jump. The float implementation agrees exactly with the
rational formula at 2^-20,2^-24 and2^-28. With unit velocity and flat bed, the
donor face flux approaches a1/128 jump. This is formula behavior, not roundoff.
The retained slope/flux continuity regressions both FAIL for the original EP
candidate: `tmp/ep-transport-continuity-v1-20260914.xml` (3PASS/2FAIL including
the branch-oracle checks). Do not xfail, delete or weaken them.

## Continuous-envelope mass candidate, separately scoped

`continuous_extremum_transport.py` replaces the hard selector with the magnitude
envelope of the original MC and curvature-limited EP slopes. Both share the
centered-slope sign and bound. This is a new derivation, not an unmodified
implementation of the published EP algorithm. Min/max envelopes are continuous;
at sign boundaries the centered or curvature cap vanishes. The claim is C0 on
strictly positive connected support, NOT C1 and NOT continuous dry-support changes.

The candidate retains the existing donor positivity bound, exact cut fallback,
same-face adjoint and three-cell MC fallback near dry support. No cell average,
depth floor, source or energy is repaired. It does not enlarge the flattened
bank band. An exact randomized check verifies that its slope equals the MC/EP
magnitude envelope, including2^-500-scale fields. The exact counterexample now
has constant slope1/4 and a face-flux gap that shrinks with the perturbation.

Eleven candidate tests pass, including the unchanged original mass/refinement/
dry-bank/adjoint controls, phase/direction/axis checks, bank support, rational
oracle and square discontinuity:
`tmp/continuous-extremum-transport-v2-20260914.xml`.
Combined earlier run retains all failed baselines:58PASS/3FAIL in11.14s at
`tmp/continuous-transport-all-controls-v1-20260914.xml`; the extra envelope
identity test was added and passed afterward. The three failures are original
MC spatial refinement and original EP slope/flux continuity. Earlier45PASS/1FAIL
and40PASS/8FAIL are not overwritten or converted into full acceptance.

## Same-crossing comparison

`audit_continuous_transport_crossings.py` repeats the original EP-coupled
trajectories unchanged, then compares both mass operators at ALL29 recorded
crossings using the same original recovered layer velocities. It explicitly
checks original mass-gap values and all eight final endpoint hashes.

Report: `tmp/south-fork-continuous-transport-crossings-v1-20260914.json`.
For the new mass operator every first-to-last gap ratio is between99.999968
and100.000019 for a100x input-distance reduction. Largest final mass-rate gap
is4.595877e-8. Seed2207 changes from0.005834221 to2.281252e-8; seed2206 from
0.000399662 to4.595877e-8. This removes the measured mass discontinuities on
these states, not the pressure-gradient discontinuities or all possible failures.

The continuous candidate has NOT been used to evolve a new coupled trajectory,
and the default research stage remains the recorded EP model. No gameplay
switch, native timing improvement, wetting/entropy/open-boundary qualification
or full moving-source acceptance is claimed.

NEXT: derive a pressure-energy reconstruction with a continuous depth gradient
on these original variable-bed states, keeping its exact independent derivative,
positive columns, bed barriers and both dispersion poles. A C0 mass limiter
alone is insufficient for that C1 requirement. Then rerun the original spatial,
energy and temporal controls with matched transport, followed by actual dry-bank,
moving-source, native-cost and visual qualification. Do not substitute a flat-bed
or shorter/easier history. Terrain, later rivers, crew and release remain required.

## Original river cook and frozen histories

All five original long handles were directly confirmed live at turn start;
no original process was restarted, suspended or reset. Both dependency guards
rechecked at finish:417/422 files, zero changes. All new diagnostic processes
are terminal. The EP face builder's later class-dispatch refactor preserves
the original actions and eight evolution endpoints in the final comparison.

Cook83142 passed9100 seconds and continued beyond9101.5/local22030. Completed
local22000 checkpoint passes BOTH audits:
`tmp/south-fork-expanded-9100s-state-v1-20260914.json` and
`tmp/south-fork-expanded-9100s-banks-v1-20260914.json`.
All5,382,400 cells finite; all86,720 artificial bank cells exactly dry;
1,084 bank faces and2,276 shared directed tile faces. Maximum depth3.7768056208m,
speed6.2207233226m/s, volume2,561,696.312470m3. Snapshot/driver volume difference
4.190952e-9m3; maximum step conservation residual1.441914e-8m3.

Depth SHA256: `d4ee60568623428bffd863dcfa21a01278d2d31534832dfda96da88240d7db37`.
Outflow102.8957142698m3/s versus inflow45.3069545472m3/s: STILL UNSETTLED,
not a normal-map acceptance. Next complete9200 seconds/local24000 needs BOTH
audits after the completion marker exists. No final commit or goal completion.
