# Water Solver Strategy Decision

Written July 15, 2026. This memo records the decision made after the uncalibrated C++ solver truth run and the honest Milestone 16 parity-gate change.

**Owner decision: Option B - build a real well-balanced finite-volume shallow-water core.** Recorded July 15, 2026.

## Decision required

Choose the validation target for the custom C++ water runtime:

- **Option A - game-feel model:** stop requiring cell-field parity with GeoClaw. Validate qualitative feature correctness, bounded conservation error, numerical stability, determinism, raft response, and runtime budget instead.
- **Option B - real shallow-water solver:** replace the fixture-conditioned approximation with a well-balanced finite-volume shallow-water core and keep GeoClaw field parity as a release gate.

Option B is authoritative for subsequent solver decomposition and implementation. Live custom-water stepping remains disabled in Unreal until the genuine solver-parity gate passes; frozen reference playback is visualization evidence only.

## Measured baseline

The frozen 40-row Milestone 16 matrix was rerun with fixture profile replay, fixture correction chains, boundary exceptions, and fixture-kind source treatments disabled. The source evidence is `physics/reports/solver_truth_baseline/uncalibrated_baseline.json`.

| Evidence class | Passing | Total | Meaning |
| --- | ---: | ---: | --- |
| Genuine uncalibrated solver parity | 6 | 40 | Base C++ dynamics pass the existing numerical thresholds. |
| Genuine uncalibrated solver failures | 34 | 40 | Base dynamics fail one or more field, wet/dry, conservation, slope, Froude, probe, cross-section, or feature checks. |
| Calibrated reference playback | 34 | 40 | Existing calibrated rows can reproduce stored GeoClaw evidence but do not validate solver dynamics. |
| Raw calibrated threshold checks | 40 | 40 | Diagnostic compatibility only; not an approval metric. |

The six genuine passes are flat pool in both modes, finite-volume uniform channel, reduced wet/dry shoreline, and sloping Manning channel in both modes. No rafting-feature case, South Fork real-world case, or stitched cascading reach/drop case passes uncalibrated.

## Option A - Re-scope to game feel

Treat the reduced solver as a stable, deterministic feature field for gameplay and rendering rather than as a GeoClaw-equivalent physical model.

The release gate would require:

- bounded mass, momentum, and energy error with no forcing allowed to conceal a failed conservation check;
- qualitative and guide-reviewed behavior for holes, boils, laterals, eddy lines, wave trains, shelves, boulder effects, pins/releases, and flips across flow bands;
- stable raft coupling, crew high-side and weight-distribution response, wet/dry behavior, deterministic replay, and target-platform performance;
- explicit manifest provenance separating authored forcing, generated visuals, and simulated state.

GeoClaw would remain an offline design reference, but field-level GeoClaw parity would no longer be an approval requirement. Fixture replay and per-fixture numerical correction machinery should then be removed because it cannot prove the new target and creates maintenance risk.

**Advantages:** shortest route to a tunable game; easier runtime budgeting; authored feature controls become first-class rather than disguised numerical fixes.

**Risks:** behavior between reviewed fixtures and flow bands is less trustworthy; stitched reaches, wet/dry transitions, and unusual geometry need much broader gameplay testing; marketing and documentation must not claim predictive hydraulic fidelity.

## Option B - Build a real finite-volume core

Implement a well-balanced Godunov-style finite-volume shallow-water solver with hydrostatic reconstruction, a documented approximate Riemann flux such as HLL or HLLC, positivity-preserving wet/dry fronts, consistent bed-slope and friction source treatment, and conservative reach-boundary exchange.

The work should proceed in this order:

1. Freeze the current 40-row matrix and Milestone 17 analytic fixtures as non-negotiable regression evidence.
2. Extract boundary handling, reconstruction/flux, source terms, wet/dry logic, feature forcing, and report IO into testable modules.
3. Pass lake-at-rest, slope/friction, dam-break, wet/dry, bed-step, hydraulic-jump, and transcritical analytic guardrails without fixture-conditioned corrections.
4. Close canonical geometry and stitched reach/drop parity, then real-world South Fork and raft-coupling cases.
5. Re-enable forcing at low defaults only after the underlying unforced conservation and parity rows pass.
6. Re-run the full Milestone 16 gate and issue a new live-water report-set lock before enabling Unreal stepping.

Fixture playback may remain temporarily as a separately named debugging viewer, but it must stay outside solver approval and runtime authority.

**Advantages:** matches the project's stated requirement for flow-dependent rapid behavior and gives authored forcing a defensible physical baseline; makes the existing GeoClaw and analytic fixtures a genuine regression suite.

**Risks:** materially larger engineering effort; wet/dry, source balance, and reach interfaces are difficult; performance optimization cannot begin by weakening correctness; raft gameplay tuning waits longer for authoritative fields.

## Recommendation

Choose **Option B**.

The game design depends on hydraulic behavior changing with discharge: a hole can become sticky, wash out, or disappear; shelves and laterals move; wave trains and pin/release windows change; and the raft must react to crew weight at the right moment. Those behaviors are exactly where the uncalibrated matrix is weakest. A game-feel model remains viable, but choosing it would knowingly trade away the field-level foundation that the current design and validation roadmap expect.

Option B does not mean forbidding authored forcing. It means forcing is layered onto a solver that first passes unforced conservation, wet/dry, geometry, and stitched-boundary checks. Every force remains bounded, flow-dependent, manifest-recorded, and separately visible to validation.

## Current gate state

- Milestone 16 solver parity: **6/40 passing**.
- Reference-playback evidence: **34/40**, excluded from approval.
- GeoClaw-to-Unreal readiness: **blocked**.
- Milestone 20 report-set lock: **blocked**.
- Unreal live custom-water stepping: **disabled**; frozen playback and telemetry remain available.

Option B implementation may proceed. Fixture playback remains isolated from solver approval, and no live-water authority may be granted until the genuine solver-parity and downstream readiness gates pass.
