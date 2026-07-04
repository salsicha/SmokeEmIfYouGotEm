# Milestone 18 South Fork Median Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `south_fork_median_runnable` real-world row.

This closure adds a finite-volume South Fork median-flow single-reach GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 32 by 16 real-world grid.

The row remains feature-forcing off with `feature_strength_scale=0`, and finite-volume already runs this open-boundary comparison with initial-mass preservation disabled. The C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.64945e-07, threshold 0.25
- `slope_linf`: 4.82473e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 5.39809e-08, threshold 0.25
- `cross_section_linf`: 6.51851e-08, threshold 0.25
- `mass_drift_delta`: 2.29452e-08, threshold 0.05
- `energy_change_delta`: 7.13766e-07, threshold 0.25
- `froude_delta`: 4.996e-16, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 1.77636e-14, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 35 of 40 pass.
- Regression promotion: 61 artifacts promoted.
- Runtime profile: 70 of 70 budget runs pass, and 35 of 35 deterministic replay groups match.
- Raft coupling: 18 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Both South Fork median-flow single-reach rows now pass with feature forcing off. Remaining comparison blockers are the high-flow real-world rows and reduced cascading rows, plus the broader raft-coupling agreement gate.
