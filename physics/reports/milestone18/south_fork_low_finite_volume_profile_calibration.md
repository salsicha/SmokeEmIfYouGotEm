# Milestone 18 South Fork Low Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `south_fork_low_runnable` real-world row.

This closure adds a finite-volume South Fork low-flow single-reach GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 32 by 16 real-world grid.

The row remains feature-forcing off with `feature_strength_scale=0`, and finite-volume already runs this open-boundary comparison with initial-mass preservation disabled. The C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.36404e-07, threshold 0.25
- `slope_linf`: 4.31888e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 5.64094e-08, threshold 0.25
- `cross_section_linf`: 4.9535e-08, threshold 0.25
- `mass_drift_delta`: 2.67151e-08, threshold 0.05
- `energy_change_delta`: 3.08435e-05, threshold 0.25
- `froude_delta`: 5.32907e-15, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 1.64257e-07, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 33 of 40 pass.
- Regression promotion: 59 artifacts promoted.
- Runtime profile: 66 of 66 budget runs pass, and 33 of 33 deterministic replay groups match.
- Raft coupling: 18 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Both South Fork low-flow single-reach rows now pass with feature forcing off. Remaining comparison blockers are the median/high real-world rows and reduced cascading rows, plus the broader raft-coupling agreement gate.
