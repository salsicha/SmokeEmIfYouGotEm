# Milestone 16 Full C++ Validation Gate

Schema: `raftsim.milestone16.full_cpp_validation_gate.v0`

Decision: **BLOCKED**

| Component | Result | Passed | Failed | Total | Source |
| --- | --- | ---: | ---: | ---: | --- |
| GeoClaw Reference Runs | PASS | 20 | 0 | 20 | `reports/milestone16/geoclaw_reference_runs.json` |
| C++ Solver Runs | PASS | 40 | 0 | 40 | `reports/milestone16/cpp_solver_runs.json` |
| GeoClaw/C++ Threshold Comparisons | BLOCKED | 26 | 14 | 40 | `reports/milestone16/geoclaw_cpp_comparisons.json` |
| Geometry-Specific Validation | PASS | 6 | 0 | 6 | `reports/milestone16/geometry_validation.json` |
| Raft Coupling Validation | BLOCKED | 16 | 34 | 50 | `reports/milestone16/raft_coupling_validation.json` |
| Runtime Profile And Determinism | PASS | 78 | 0 | 78 | `reports/milestone16/runtime_profile.json` |
| Regression Promotion | PASS | 50 | 0 | 50 | `reports/milestone16/regression_promotion_manifest.json` |

## Blockers

### GeoClaw/C++ Threshold Comparisons
- lateral_wave: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- eddy_line_shear: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- eddy_line_shear: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- shallow_shelf: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- shallow_shelf: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- south_fork_low_runnable: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- south_fork_low_runnable: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- south_fork_median_runnable: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)

### Raft Coupling Validation
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- lateral_wave_side_impulse: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- lateral_wave_side_impulse: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., Canonical feature outcomes differ., Force delta exceeds the weight-normalized threshold., Torque delta exceeds the inertia-normalized threshold.)
