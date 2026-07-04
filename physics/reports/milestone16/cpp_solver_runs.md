# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.235 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.204 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.184 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.202 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.176 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.201 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.169 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.213 | no |
| canonical | constriction | reduced | 9 | PASS | 0.187 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.196 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.170 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.217 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.170 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.197 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.155 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.217 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.384 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.462 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.411 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.403 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.392 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.471 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.516 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.853 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.519 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 1.024 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.527 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.934 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.223 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.380 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.246 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.309 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.226 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.292 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.315 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.498 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.349 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.489 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.315 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.496 | 7 reaches / 1 drops |
