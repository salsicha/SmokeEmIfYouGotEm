# Milestone 16 Full C++ Validation Gate

Schema: `raftsim.milestone16.full_cpp_validation_gate.v0`

Decision: **BLOCKED**

| Component | Result | Passed | Failed | Total | Source |
| --- | --- | ---: | ---: | ---: | --- |
| GeoClaw Reference Runs | PASS | 20 | 0 | 20 | `physics/reports/milestone16/geoclaw_reference_runs.json` |
| C++ Solver Runs | PASS | 40 | 0 | 40 | `physics/reports/milestone16/cpp_solver_runs.json` |
| GeoClaw/C++ Threshold Comparisons | BLOCKED | 4 | 36 | 40 | `physics/reports/milestone16/geoclaw_cpp_comparisons.json` |
| Geometry-Specific Validation | BLOCKED | 2 | 4 | 6 | `physics/reports/milestone16/geometry_validation.json` |
| Raft Coupling Validation | BLOCKED | 7 | 43 | 50 | `physics/reports/milestone16/raft_coupling_validation.json` |
| Runtime Profile And Determinism | PASS | 12 | 0 | 12 | `physics/reports/milestone16/runtime_profile.json` |
| Regression Promotion | PASS | 11 | 0 | 11 | `physics/reports/milestone16/regression_promotion_manifest.json` |

## Blockers

### GeoClaw/C++ Threshold Comparisons
- uniform_channel: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, mass_drift_delta)
- uniform_channel: GeoClaw/C++ threshold comparison failed (field_linf)
- dam_break: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, wet_mismatch_fraction, probe_linf)
- dam_break: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- bed_step: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- bed_step: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)
- constriction: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, wet_mismatch_fraction, probe_linf)
- constriction: GeoClaw/C++ threshold comparison failed (field_linf, slope_linf, probe_linf, cross_section_linf)

### Geometry-Specific Validation
- wet_dry_shoreline: geometry family is blocked
- bed_step: geometry family is blocked
- constriction: geometry family is blocked
- drops_ledges_tailwater: geometry family is blocked

### Raft Coupling Validation
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Force-envelope outcomes differ., Force delta exceeds the weight-normalized threshold.)
- boulder_impacts: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Force delta exceeds the weight-normalized threshold.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Canonical feature outcomes differ., Force delta exceeds the weight-normalized threshold.)
- wave_train_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Canonical feature outcomes differ., Force delta exceeds the weight-normalized threshold.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Force-envelope outcomes differ., Force delta exceeds the weight-normalized threshold.)
- downstream_boil_recovery: raft coupling comparison failed (C++ raft feature checks are not passing., Force delta exceeds the weight-normalized threshold., Torque delta exceeds the inertia-normalized threshold., One-step velocity delta exceeds threshold.)
- hydraulic_hole_surf_flush: raft coupling comparison failed (GeoClaw-derived raft feature checks are not passing., C++ raft feature checks are not passing., Force delta exceeds the weight-normalized threshold., One-step velocity delta exceeds threshold.)
- downstream_boil_recovery: raft coupling comparison failed (C++ raft feature checks are not passing., Force delta exceeds the weight-normalized threshold., One-step velocity delta exceeds threshold.)
