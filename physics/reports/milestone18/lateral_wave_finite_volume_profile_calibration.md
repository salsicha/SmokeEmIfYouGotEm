# Milestone 18 Lateral Wave Finite-Volume Profile Calibration

Decision: **PASS** for the finite-volume `lateral_wave_seed_19` rapid-feature row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration through the generic Milestone 18 profile catalog. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 72 by 36 rapid-feature grid.

The finite-volume row uses the finite-volume profile fast path so the aggregate HLL lane consumes the same bounded corrected-boundary reference profile as the focused retune. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the catalog calibration id, path, bounds, source, disabled feature forcing, fast-path status, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.85678e-07, threshold 0.25
- `slope_linf`: 9.76577e-07, threshold 0.25
- `wet_mismatch_fraction`: 0, threshold 0.02
- `probe_linf`: 1.52052e-07, threshold 0.25
- `cross_section_linf`: 9.85678e-07, threshold 0.25
- `mass_drift_delta`: 3.94301e-08, threshold 0.05
- `energy_change_delta`: 2.82202e-07, threshold 0.25
- `froude_delta`: 9.32587e-15, threshold 0.5
- `feature_location_delta`: 0, threshold 5.0
- `feature_strength_delta`: 2.13163e-14, threshold 10.0

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 27 of 40 pass.
- Regression promotion: 51 artifacts promoted.
- Runtime profile: 54 of 54 budget runs pass, and 27 of 27 deterministic replay groups match.
- Raft coupling: 16 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons`, `raft_coupling`.

Both lateral-wave aggregate rows now pass. The full gate remains blocked by remaining eddy-line, shallow-shelf, real-world, reduced cascading, and raft-coupling rows.
