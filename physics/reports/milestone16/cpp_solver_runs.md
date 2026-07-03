# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.132 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.157 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.139 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.164 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.140 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.167 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.212 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.175 | no |
| canonical | constriction | reduced | 9 | PASS | 0.126 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.126 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.130 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.179 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.132 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.164 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.121 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.167 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.365 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.433 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.363 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.363 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.486 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.913 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.481 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.806 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.574 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.803 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.482 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.886 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.194 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.268 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.189 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.255 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.184 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.258 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.353 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.436 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.276 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.462 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.319 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.485 | 7 reaches / 1 drops |
