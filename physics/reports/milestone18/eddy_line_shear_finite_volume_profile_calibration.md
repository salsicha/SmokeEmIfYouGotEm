# Milestone 18 Eddy Line Shear Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `eddy_line_shear_seed_20` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The finite-volume row uses the finite-volume profile fast path so the aggregate HLL lane consumes the same bounded corrected-boundary reference profile as the focused retune. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

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

- GeoClaw/C++ threshold comparisons: 29 of 40 pass.
- Regression promotion: 54 artifacts promoted.
- Runtime profile: 58 of 58 budget runs pass, and 29 of 29 deterministic replay groups match.
- Raft coupling: 17 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Both eddy-line/shear aggregate rows now pass. The full gate remains blocked by remaining shallow-shelf, real-world, reduced cascading, and raft-coupling rows.
