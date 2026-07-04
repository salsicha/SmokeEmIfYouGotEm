# Milestone 18 South Fork Low Reduced Profile Calibration

Decision: **PASS** for the reduced `south_fork_low_runnable` real-world row.

This closure adds a low-flow South Fork single-reach GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 32 by 16 real-world grid.

The row remains feature-forcing off with `feature_strength_scale=0`. The aggregate reduced config now disables initial-mass preservation for `south_fork_low_runnable`, matching the open-boundary profile comparison instead of mass-correcting the C++ state away from the recorded GeoClaw reference.

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

- GeoClaw/C++ threshold comparisons: 32 of 40 pass.
- Regression promotion: 58 artifacts promoted.
- Runtime profile: 64 of 64 budget runs pass, and 32 of 32 deterministic replay groups match.
- Raft coupling: 18 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Remaining comparison blockers are the finite-volume low-flow row, median/high real-world rows, and reduced cascading rows, plus the broader raft-coupling agreement gate.
