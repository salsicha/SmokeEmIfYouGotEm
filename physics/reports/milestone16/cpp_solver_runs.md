# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.083 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.112 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.090 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.112 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.096 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.123 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.091 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.123 | no |
| canonical | constriction | reduced | 9 | PASS | 0.073 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.072 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.086 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.134 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.094 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.118 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.100 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.176 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.307 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.743 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.427 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.844 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.437 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.763 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.521 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.880 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.455 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.838 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.435 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.859 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.142 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.218 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.143 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.218 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.141 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.219 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.309 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.411 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.234 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.403 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.232 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.476 | 7 reaches / 1 drops |
