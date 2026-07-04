# Milestone 18 South Fork Cascading Low Reduced Profile Calibration

Decision: **PASS** for the reduced `south_fork_cascading_low_runnable` stitched whole-window row.

This closure adds a reduced South Fork low-flow cascading GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses stitched whole-window normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 56 by 20 cascading grid, so reach/drop seams remain visible to validation.

The row remains feature-forcing off with `feature_strength_scale=0`. The aggregate reduced config now disables initial-mass preservation for `south_fork_cascading_low_runnable`, matching the open-boundary profile comparison instead of mass-correcting the C++ state away from the recorded GeoClaw reference.

## Passing Checks

- `field_linf`: 5.05502e-07, threshold 0.25
- `slope_linf`: 1.26376e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 5.77093e-08, threshold 0.25
- `cross_section_linf`: 6.40692e-08, threshold 0.25
- `mass_drift_delta`: 4.22086e-10, threshold 0.05
- `energy_change_delta`: 1.67364e-09, threshold 0.25
- `froude_delta`: 1.59872e-14, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 5.68434e-14, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 38 of 40 pass.
- Regression promotion: 68 artifacts promoted.
- Runtime profile: 76 of 76 budget runs pass, and 38 of 38 deterministic replay groups match.
- Raft coupling: 22 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Remaining comparison blockers are the median/high reduced cascading rows, plus the broader raft-coupling agreement gate.
