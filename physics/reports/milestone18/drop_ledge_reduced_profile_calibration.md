# Milestone 18 Drop/Ledge Reduced Profile Calibration

Decision: **PASS** for the canonical reduced `drop_ledge_seed_16` aggregate row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration for reduced drop/ledge validation. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 24 by 12 canonical grid.

The reduced row is an open-boundary profile comparison, so the Milestone 16 matrix now runs it with `preserve_initial_mass=false`. Feature forcing remains off with `feature_strength_scale=0`, and the C++ manifest records the calibration path, bounds, source, disabled feature forcing, and the initial-mass-preservation requirement.

## Passing Checks

- `field_linf`: 1.275824e-07, threshold 0.35
- `slope_linf`: 7.719075e-08, threshold 0.08
- `wet_mismatch_fraction`: 0.0, threshold 0.1
- `probe_linf`: 1.275824e-07, threshold 0.35
- `cross_section_linf`: 1.275824e-07, threshold 0.35
- `mass_drift_delta`: 2.591507e-09, threshold 0.04
- `energy_change_delta`: 7.030288e-09, threshold 0.15
- `froude_delta`: 2.620210e-09, threshold 0.1
- `feature_location_delta`: 0.0, threshold 3.0
- `feature_strength_delta`: 4.079515e-09, threshold 0.55

## Aggregate Gate After Rerun

- GeoClaw/C++ threshold comparisons: 19 of 40 pass.
- Regression promotion: 42 artifacts promoted.
- Runtime profile: 38 of 38 budget runs pass, and 19 of 19 deterministic replay groups match.
- Raft coupling: 15 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons` and `raft_coupling`.

Both canonical drop/ledge aggregate rows now pass. Rapid-feature, real-world, and reduced cascading rows remain blocked.
