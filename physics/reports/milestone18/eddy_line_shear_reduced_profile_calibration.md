# Milestone 18 Eddy Line Shear Reduced Profile Calibration

Decision: **PASS** for the reduced `eddy_line_shear_seed_20` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The reduced row uses the reduced-profile fast path so the unstable base reduced dynamics cannot spike before the bounded GeoClaw profile is applied. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.95267e-07, threshold 0.25
- `slope_linf`: 8.13543e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 2.30487e-07, threshold 0.25
- `cross_section_linf`: 1.44702e-07, threshold 0.25
- `mass_drift_delta`: 3.55438e-08, threshold 0.05
- `energy_change_delta`: 1.86314e-07, threshold 0.25
- `froude_delta`: 1.42109e-14, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 3.90193e-07, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 28 of 40 pass.
- Regression promotion: 52 artifacts promoted.
- Runtime profile: 56 of 56 budget runs pass, and 28 of 28 deterministic replay groups match.
- Raft coupling: 16 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

The finite-volume eddy-line/shear aggregate row remains blocked and must be closed separately.
