# Milestone 18 Constriction Reduced Profile Calibration

Decision: **PASS** for the canonical reduced `constriction_seed_16` aggregate row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration for reduced constriction validation. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 24 by 12 canonical grid.

The reduced row is an open-boundary profile comparison, so the Milestone 16 matrix now runs it with `preserve_initial_mass=false`. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the calibration path, bounds, source, disabled feature forcing, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 9.062128e-07, threshold 0.35
- `slope_linf`: 9.062130e-07, threshold 0.08
- `wet_mismatch_fraction`: 0.0, threshold 0.1
- `probe_linf`: 5.099967e-08, threshold 0.35
- `cross_section_linf`: 2.192242e-08, threshold 0.35
- `mass_drift_delta`: 5.167606e-09, threshold 0.04
- `energy_change_delta`: 1.029569e-08, threshold 0.15
- `froude_delta`: 5.247716e-10, threshold 0.1
- `feature_location_delta`: 0.0, threshold 3.0
- `feature_strength_delta`: 2.103553e-10, threshold 0.55

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 18 of 40 pass.
- Regression promotion: 41 artifacts promoted.
- Runtime profile: 36 of 36 budget runs pass, and 18 of 18 deterministic replay groups match.
- Raft coupling: 15 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons` and `raft_coupling`.

Both canonical constriction aggregate rows now pass. Reduced drop/ledge is the next canonical aggregate blocker.
