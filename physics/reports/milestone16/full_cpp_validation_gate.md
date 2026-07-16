# Milestone 16 Full C++ Validation Gate

Schema: `raftsim.milestone16.full_cpp_validation_gate.v0`

Decision: **BLOCKED**

| Component | Result | Passed | Failed | Total | Source |
| --- | --- | ---: | ---: | ---: | --- |
| GeoClaw Reference Runs | PASS | 20 | 0 | 20 | `reports/milestone16/geoclaw_reference_runs.json` |
| C++ Solver Runs | PASS | 40 | 0 | 40 | `reports/milestone16/cpp_solver_runs.json` |
| GeoClaw/C++ Solver-Parity Comparisons | BLOCKED | 6 | 34 | 40 | `reports/milestone16/geoclaw_cpp_comparisons.json` |
| Geometry-Specific Validation | PASS | 6 | 0 | 6 | `reports/milestone16/geometry_validation.json` |
| Raft Coupling Validation | PASS | 50 | 0 | 50 | `reports/milestone16/raft_coupling_validation.json` |
| Runtime Profile And Determinism | PASS | 120 | 0 | 120 | `reports/milestone16/runtime_profile.json` |
| Regression Promotion | PASS | 98 | 0 | 98 | `reports/milestone16/regression_promotion_manifest.json` |

## Blockers

### GeoClaw/C++ Solver-Parity Comparisons
- uniform_channel: row does not provide passing solver-parity evidence (fixture_scoped_uniform_channel_reduced_slope_profile_balance)
- dam_break: row does not provide passing solver-parity evidence (fixture_scoped_dam_break_geoclaw_profile_calibration)
- dam_break: row does not provide passing solver-parity evidence (fixture_scoped_dam_break_geoclaw_profile_calibration)
- bed_step: row does not provide passing solver-parity evidence (fixture_scoped_bed_step_reduced_geoclaw_profile_calibration)
- bed_step: row does not provide passing solver-parity evidence (fixture_scoped_bed_step_finite_volume_hydrostatic_face_source)
- constriction: row does not provide passing solver-parity evidence (fixture_scoped_constriction_reduced_geoclaw_profile_calibration, constriction_reduced_geoclaw_profile_calibration.enabled)
- constriction: row does not provide passing solver-parity evidence (fixture_scoped_constriction_finite_volume_geoclaw_profile_calibration, constriction_finite_volume_geoclaw_profile_calibration.enabled)
- wet_dry_shoreline: row does not provide passing solver-parity evidence (fixture_scoped_wet_dry_reconstruction)
