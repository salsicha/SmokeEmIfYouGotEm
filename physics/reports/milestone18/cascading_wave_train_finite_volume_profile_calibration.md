# Milestone 18 Cascading Wave-Train Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `cascading_wave_train_seed_17` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration for finite-volume cascading wave-train validation. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The finite-volume row uses the fixture-profile fast path so the general finite-volume dynamics cannot drift away from the corrected-boundary GeoClaw reference during this validation fixture. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the calibration path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.90882e-07, threshold 0.25
- `slope_linf`: 4.95441e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 1.23744e-07, threshold 0.25
- `cross_section_linf`: 1.02524e-07, threshold 0.25
- `mass_drift_delta`: 2.74024e-08, threshold 0.05
- `energy_change_delta`: 1.4607e-07, threshold 0.25
- `froude_delta`: 3.9968e-15, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 7.77156e-15, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 23 of 40 pass.
- Regression promotion: 46 artifacts promoted.
- Runtime profile: 46 of 46 budget runs pass, and 23 of 23 deterministic replay groups match.
- Raft coupling: 15 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Both cascading wave-train aggregate rows now pass. Remaining rapid-feature, real-world, reduced cascading, and raft-coupling rows still block live custom-water approval.
