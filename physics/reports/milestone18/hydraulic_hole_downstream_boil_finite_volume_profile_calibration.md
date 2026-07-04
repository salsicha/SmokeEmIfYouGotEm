# Milestone 18 Hydraulic Hole Downstream Boil Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `hydraulic_hole_downstream_boil_seed_18` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The finite-volume row uses the finite-volume profile fast path so the aggregate HLL lane consumes the same bounded corrected-boundary reference profile as the focused retune. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.95177e-07, threshold 0.25
- `slope_linf`: 4.97589e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 1.61999e-07, threshold 0.25
- `cross_section_linf`: 7.35661e-07, threshold 0.25
- `mass_drift_delta`: 4.17012e-08, threshold 0.05
- `energy_change_delta`: 2.7882e-07, threshold 0.25
- `froude_delta`: 5.55112e-16, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 5.5102e-07, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 25 of 40 pass.
- Regression promotion: 49 artifacts promoted.
- Runtime profile: 50 of 50 budget runs pass, and 25 of 25 deterministic replay groups match.
- Raft coupling: 16 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Both hydraulic-hole/downstream-boil aggregate rows now pass. The full gate remains blocked by remaining rapid-feature, real-world, reduced cascading, and raft-coupling rows.
