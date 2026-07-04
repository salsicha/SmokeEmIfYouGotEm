# Milestone 16 Full C++ Validation Gate

Schema: `raftsim.milestone16.full_cpp_validation_gate.v0`

Decision: **BLOCKED**

| Component | Result | Passed | Failed | Total | Source |
| --- | --- | ---: | ---: | ---: | --- |
| GeoClaw Reference Runs | PASS | 20 | 0 | 20 | `reports/milestone16/geoclaw_reference_runs.json` |
| C++ Solver Runs | PASS | 40 | 0 | 40 | `reports/milestone16/cpp_solver_runs.json` |
| GeoClaw/C++ Threshold Comparisons | PASS | 40 | 0 | 40 | `reports/milestone16/geoclaw_cpp_comparisons.json` |
| Geometry-Specific Validation | PASS | 6 | 0 | 6 | `reports/milestone16/geometry_validation.json` |
| Raft Coupling Validation | BLOCKED | 30 | 20 | 50 | `reports/milestone16/raft_coupling_validation.json` |
| Runtime Profile And Determinism | PASS | 120 | 0 | 120 | `reports/milestone16/runtime_profile.json` |
| Regression Promotion | PASS | 78 | 0 | 78 | `reports/milestone16/regression_promotion_manifest.json` |

## Blockers

### Raft Coupling Validation
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- lateral_wave_side_impulse: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
- lateral_wave_side_impulse: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing.)
