# Total-depth finite-depth coupling — September 12

Previous goal turn was progress: the higher-order hydrostatic bank control passed
5 s and 20 s, with no retries. This turn restores and evaluates finite-depth
linear behavior, but exposes a nonlinear pressure limitation. The entire goal
remains active. No Unreal source/shader/map/material/save changes, build, engine
motion capture, reference-video playback or new FPS claim in this turn.
Ordinary play still uses the previously integrated finite-depth detail model,
with experimental strain OFF. Its latest measured 21.571211 FPS / p95 52.6052 ms
still fails the current 30 FPS target.

## Implemented, not promoted

`total_depth_pressure.py` solves for the two pressure-potential corrections
directly instead of subtracting nearly equal absolute elevations afterward.
It retains the existing continued-fraction coefficients and 40 iterations per
RK stage. The initial four-neighbor convergence bound failed a small linear
response check. Removing null periodic self-edges and using the actual row
off-diagonal/diagonal bound passes that check without adding iterations.

`total_depth_bank_replay.py --second-order --dispersive` evolves total h/hu/hv
and uses the same MC face derivative for the pressure correction as for the
hydrostatic pressure. The wet graph is rebuilt from the final hydrostatic
reconstructed faces, including the local partially dry treatment. Pressure
cannot communicate through a dry reconstructed face, outside a wall boundary,
or through an invalid supplied graph. No minimum film, height/momentum repair,
velocity cap, or relaxed timestep floor is introduced.

This is a local-depth rational pressure approximation, NOT the fully nonlinear
Green–Naghdi or variable-bathymetry Dirichlet-to-Neumann operator. The existing
hydrostatic energy diagnostic does not include nonlocal pressure energy and is
explicitly labeled accordingly. Passing that diagnostic cannot qualify it.

## Actual difficult bank still rejects physical acceptance

Both first comparisons use the same paired 15 s input and four hashes described
in [the higher-order control](normal-river-high-order-bank.md). Reports are
`tmp/south-fork-total-depth-dispersive-bank-vN-20260912.json`, with final arrays
and implementation/dependency hashes.

| Trial | Pressure graph | Result |
| --- | --- | --- |
| v1 | Cell-average hydrostatic connectivity | 5 s, 600 steps, zero retries/volume error; max depth 7.700788716 m |
| v2 | Same final reconstructed faces as transport | 5 s, 600 steps, zero retries/volume error; max depth 7.694617608 m |
| v3 | v2 plus explicit graph-input validation | Identical numerical result to v2; final implementation/dependency hashes retained |

Final main-script SHA:
`92861287a6665f05f9a76569d5050e690efd862e2169537b2ea6a6e3c81cf681`.
Final pressure-module SHA:
`d1392f3758dba3051b324f227415bd32248f3058addf111e75389741f330927f`.
The comparison report precedes the validation-only change and retains its own
dependency hashes. v3 reruns the actual bank with the final guarded module.

v2's peak accepted-state speed is 7.923172617 m/s. Positive depth and bounded
speed are useful but insufficient: the concentrated crest is not accepted as
realistic. In v1 the deepest cell is (x20,y84), bed 4.551208496 m, surface
12.251997212 m, speed 1.01525 m/s. Initial maximum wet surface and specific head
are 9.594018803 and 9.594206180 m. This is not presented as a mathematical
maximum-principle violation—unsteady waves can concentrate energy—but it is a
major discrepancy from the 3.667 m maximum-depth hydrostatic control requiring
nonlinear/reference validation. Fixing connectivity barely changes the result.

## Analytic comparison separates linear and nonlinear behavior

`audit_total_depth_dispersion.py` writes
`tmp/south-fork-total-depth-dispersion-comparison-v1-20260912.json`.
The small-wave cases use mean depth 1.5 m, current 0.4 m/s, amplitude 1e-5 m,
32 cells per wavelength, and one analytic period. These are diagnostic checks,
not a new release gate or a claim about production-grid resolution.

| Wavelength | Wrapped phase error, cycles | Final / initial amplitude |
| --- | --- | --- |
| 2 m | 0.00682329 | 0.981590 |
| 4 m | 0.00417541 | 0.988284 |
| 12 m | 0.00339874 | 0.991816 |

All three coupled cases pass the diagnostic 0.03-cycle / 0.9–1.1 amplitude
checks; the nondispersive controls fail the combined checks. Phase is explicitly
wrapped, not an unwrapped speed measurement; the pressure-symbol tests provide
an additional independent check.

The finite-amplitude comparison uses the exact SGN solitary wave from
[Guermond et al., equation 7.1](https://people.tamu.edu/~guermond/PUBLICATIONS/GKPT_WaterWaves_2022.pdf),
with h0=1.5 m, amplitude 0.45 m, 96 m periodic domain and 4 s propagation. It is
a reference-model comparison, not an exact solution of this pressure candidate.
The isolated solitary profile also has small nonzero tails at the periodic
domain boundary; it is not an exact periodic solitary-wave solution.
Errors are normalized by wave elevation rather than the large background depth.

| Cell size | Relative surface L1 discrepancy | Peak amplitude ratio | Peak speed discrepancy | Total momentum change |
| --- | --- | --- | --- | --- |
| 0.5 m | 0.104162 | 1.034556 | +2.75780% | +0.0133862 m3/s |
| 0.25 m | 0.096364 | 1.070647 | +1.46322% | +0.0102796 m3/s |

The nondispersive comparison has 0.426–0.431 relative surface discrepancy and
17.0–20.1% peak-speed discrepancy. Dispersion improves that comparison, but the
candidate's shape discrepancy persists on refinement, its peak amplitude error
grows, and it changes total momentum in a flat periodic domain. The hydrostatic
controls conserve that momentum to approximately 3e-15 m3/s. Do NOT promote
the candidate based on its small-amplitude passes or its larger visible crest.

All 87 focused tests pass (16 new pressure tests plus the previous 71). They
cover matrix solves, linear response, rest states, datum invariance, graph
validation, bank admissibility, capture reading and performance/release parsers.
They do not assert full nonlinear physical acceptance.

## Next action: nonlinear pressure, then playable coupling

The next implementation must include consistent nonlinear nonhydrostatic
acceleration/pressure and bathymetric terms, not simply extend `-g*h*grad(C)`
to large crests. The fully nonlinear SGN formulation includes depth-cubed
velocity-gradient terms absent here; see the
[SGN equations and conserved quantities](https://numericalmathematics.github.io/DispersiveShallowWater.jl/stable/overview/#Serre-Green-Naghdi).
The [variable-bottom Whitham–Green–Naghdi formulation](https://doi.org/10.1016/j.jde.2024.05.018)
is a relevant full-dispersion reference. These references are design inputs,
not an assertion that their algorithms or proofs have been implemented.

Retain the verified hydrostatic wet/dry treatment, finite-depth linear response,
40-iteration/solver/memory budgets and original physical/visual requirements.
Test nonlinear wave shape and periodic momentum as well as the same real bank
before GPU promotion. Do not replace the model with the nondispersive control
because it is easier to pass. Then complete source/mean/moving-window coupling,
shared rendered/contact behavior, actual reference-matched breaking/froth and
30 FPS qualification. Current GPU flow contains H/U/V/activity; bed is captured
only diagnostically, so production bed ownership/upload must also be handled.

The long hydraulic cook remains live without restart. Last both-audited state
is 2800 s; runtime remains the previously audited 600 s state. 2900/local18000
is the next checkpoint needing independent state AND artificial-bank audits.
All terrain/boulders/collision, remaining rivers in order, crew, normalization,
release and final-commit work stays active.
