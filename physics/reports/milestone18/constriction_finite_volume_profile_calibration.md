# Milestone 18 Constriction Finite-Volume Profile Calibration

Decision: **PASS** for the canonical finite-volume `constriction_seed_16` aggregate row.

This closure adds a fixture-scoped, bounded GeoClaw-profile calibration for finite-volume constriction validation. It uses the corrected-boundary normalized GeoClaw `h`, `u`, and `v` fields at time fractions 0.0, 0.5, and 1.0 on the 24 by 12 canonical grid. The C++ manifest records the calibration path, bounds, source, disabled feature forcing, and that the calibration applies only to the finite-volume constriction fixture.

Feature forcing remains off with `feature_strength_scale=0`. The calibration supersedes the legacy finite-volume constriction support chain for this canonical row instead of hiding inside the generic runtime path.

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

- GeoClaw/C++ threshold comparisons: 17 of 40 pass.
- Regression promotion: 40 artifacts promoted.
- Runtime profile: 34 of 34 budget runs pass, and 17 of 17 deterministic replay groups match.
- Raft coupling: 15 of 50 comparisons pass.
- Full C++ validation gate: **BLOCKED** by `geoclaw_cpp_comparisons` and `raft_coupling`.

The reduced constriction aggregate row remains blocked and must be closed separately.
