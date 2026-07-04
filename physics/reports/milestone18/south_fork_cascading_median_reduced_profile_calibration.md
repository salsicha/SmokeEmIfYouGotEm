# Milestone 18 South Fork Cascading Median Reduced Profile Calibration

Decision: **PASS** for the reduced `south_fork_cascading_median_runnable` stitched whole-window row.

This closure adds a reduced South Fork median-flow cascading GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses stitched whole-window normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 56 by 20 cascading grid, so reach/drop seams remain visible to validation.

The row remains feature-forcing off with `feature_strength_scale=0`. The aggregate reduced config now disables initial-mass preservation for `south_fork_cascading_median_runnable`, matching the open-boundary profile comparison instead of mass-correcting the C++ state away from the recorded GeoClaw reference.

## Passing Checks

- `field_linf`: 9.55311e-07, threshold 0.35
- `slope_linf`: 2.38828e-07, threshold 0.08
- `wet_mismatch_fraction`: 0, threshold 0.1
- `probe_linf`: 1.63299e-07, threshold 0.35
- `cross_section_linf`: 1.60418e-07, threshold 0.35
- `mass_drift_delta`: 4.85299e-09, threshold 0.04
- `energy_change_delta`: 4.42318e-09, threshold 0.15
- `froude_delta`: 1.33227e-14, threshold 0.1
- `feature_location_delta`: 0, threshold 3.0
- `feature_strength_delta`: 5.77316e-14, threshold 0.55

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 39 of 40 pass.
- Regression promotion: 73 artifacts promoted.
- Runtime profile: 78 of 78 budget runs pass, and 39 of 39 deterministic replay groups match.
- Raft coupling: 26 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Remaining comparison blocker is the high-flow reduced cascading row, plus the broader raft-coupling agreement gate.
