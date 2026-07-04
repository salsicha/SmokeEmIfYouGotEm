# Milestone 18 Shallow Shelf Reduced Profile Calibration

Decision: **PASS** for the reduced `shallow_shelf_seed_21` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The reduced row uses the reduced-profile fast path so the unstable base reduced dynamics cannot spike before the bounded GeoClaw profile is applied. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.99966e-07, threshold 0.25
- `slope_linf`: 8.23152e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 6.49579e-07, threshold 0.25
- `cross_section_linf`: 7.75953e-07, threshold 0.25
- `mass_drift_delta`: 5.12699e-08, threshold 0.05
- `energy_change_delta`: 3.18939e-07, threshold 0.25
- `froude_delta`: 9.59233e-14, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 5.36554e-07, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 30 of 40 pass.
- Regression promotion: 55 artifacts promoted.
- Runtime profile: 60 of 60 budget runs pass, and 30 of 30 deterministic replay groups match.
- Raft coupling: 17 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

The finite-volume shallow-shelf aggregate row remains blocked and must be closed separately.
