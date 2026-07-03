# Milestone 16 Full C++ Validation Gate

Schema: `raftsim.milestone16.full_cpp_validation_gate.v0`

Decision: **BLOCKED**

| Component | Result | Passed | Failed | Total | Source |
| --- | --- | ---: | ---: | ---: | --- |
| GeoClaw Reference Runs | PASS | 20 | 0 | 20 | `reports/milestone16/geoclaw_reference_runs.json` |
| C++ Solver Runs | PASS | 40 | 0 | 40 | `reports/milestone16/cpp_solver_runs.json` |
| GeoClaw/C++ Threshold Comparisons | BLOCKED | 13 | 27 | 40 | `reports/milestone16/geoclaw_cpp_comparisons.json` |
| Geometry-Specific Validation | PASS | 6 | 0 | 6 | `reports/milestone16/geometry_validation.json` |
| Raft Coupling Validation | BLOCKED | 15 | 35 | 50 | `reports/milestone16/raft_coupling_validation.json` |
| Runtime Profile And Determinism | PASS | 39 | 0 | 39 | `reports/milestone16/runtime_profile.json` |
| Regression Promotion | PASS | 36 | 0 | 36 | `reports/milestone16/regression_promotion_manifest.json` |

## Blockers

### GeoClaw/C++ Threshold Comparisons
- dam_break: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- dam_break: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- bed_step: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, mass_drift_delta)
- constriction: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, wet_mismatch_fraction, probe_linf)
- constriction: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, feature_strength_delta)
- drop_ledge: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- boulder_garden: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, wet_mismatch_fraction, probe_linf)
- boulder_garden: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)

### Raft Coupling Validation
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Force-envelope outcomes differ., Force delta exceeds the weight-normalized threshold.)
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Canonical feature outcomes differ., Force delta exceeds the weight-normalized threshold.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Canonical feature outcomes differ.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- downstream_boil_recovery: raft coupling comparison failed (C++ raft feature checks are not passing., Force delta exceeds the weight-normalized threshold., Torque delta exceeds the inertia-normalized threshold.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- lateral_wave_side_impulse: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
