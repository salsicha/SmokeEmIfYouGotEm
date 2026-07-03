# Milestone 18 Boulder Garden Reduced Profile Calibration

Decision: **PASS** for the reduced `boulder_garden_seed_16` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration for reduced boulder-garden validation. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The reduced row uses the reduced-profile fast path so the unstable base reduced dynamics cannot spike before the bounded GeoClaw profile is applied. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the calibration path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.778112e-07, threshold 0.25
- `slope_linf`: 4.906183e-07, threshold 0.25
- `wet_mismatch_fraction`: 0.0, threshold 0.02
- `probe_linf`: 1.075490e-07, threshold 0.25
- `cross_section_linf`: 1.131798e-07, threshold 0.25
- `mass_drift_delta`: 4.204819e-08, threshold 0.05
- `energy_change_delta`: 3.413354e-07, threshold 0.25
- `froude_delta`: 3.535862e-08, threshold 0.5
- `feature_location_delta`: 0.0, threshold 5.0
- `feature_strength_delta`: 0.001096, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 20 of 40 pass.
- Regression promotion: 43 artifacts promoted.
- Runtime profile: 40 of 40 budget runs pass, and 20 of 20 deterministic replay groups match.
- Raft coupling: 15 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons` and `raft_coupling`.

The finite-volume boulder-garden aggregate row remains blocked and must be closed separately.
