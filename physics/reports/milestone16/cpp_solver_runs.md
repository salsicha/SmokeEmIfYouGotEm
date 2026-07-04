# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.175 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.211 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.187 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.251 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.246 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.225 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.187 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.219 | no |
| canonical | constriction | reduced | 9 | PASS | 0.172 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.170 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.177 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.224 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.191 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.211 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.179 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.294 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.402 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.413 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.407 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.404 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.451 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.439 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.408 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.860 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.608 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.891 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.543 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.946 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.243 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.309 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.237 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.324 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.248 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.314 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.325 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.614 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.334 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.491 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.330 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.502 | 7 reaches / 1 drops |
