# Milestone 18 South Fork High Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `south_fork_high_runnable` real-world row.

This closure adds a finite-volume South Fork high-flow single-reach GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 32 by 16 real-world grid.

The row remains feature-forcing off with `feature_strength_scale=0`, and finite-volume already runs this open-boundary comparison with initial-mass preservation disabled. The C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.9278e-07, threshold 0.25
- `slope_linf`: 4.9639e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 1.89334e-07, threshold 0.25
- `cross_section_linf`: 1.89334e-07, threshold 0.25
- `mass_drift_delta`: 1.40094e-08, threshold 0.05
- `energy_change_delta`: 1.32242e-07, threshold 0.25
- `froude_delta`: 8.88178e-16, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 7.54952e-15, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 37 of 40 pass.
- Regression promotion: 63 artifacts promoted.
- Runtime profile: 74 of 74 budget runs pass, and 37 of 37 deterministic replay groups match.
- Raft coupling: 18 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

All South Fork single-reach real-world rows now pass with feature forcing off. Remaining comparison blockers are the reduced cascading rows, plus the broader raft-coupling agreement gate.
