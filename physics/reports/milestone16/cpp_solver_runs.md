# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.071 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.101 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.079 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.110 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.086 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.127 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.086 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.130 | no |
| canonical | constriction | reduced | 9 | PASS | 0.077 | no |
| canonical | constriction | finite_volume | 9 | PASS | 6.138 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.074 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.132 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.078 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.110 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.077 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.118 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.464 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.926 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.491 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.858 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.482 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.994 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.471 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.950 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.489 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.841 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.576 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.879 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.138 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.216 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.140 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.217 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.138 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.222 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.323 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.444 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.244 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.431 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.233 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.431 | 7 reaches / 1 drops |
