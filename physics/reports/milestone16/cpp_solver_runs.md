# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.261 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.312 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.260 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.281 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.262 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.288 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.258 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.285 | no |
| canonical | constriction | reduced | 9 | PASS | 0.241 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.242 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.249 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.294 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.257 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.280 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.242 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.287 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.449 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.451 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.453 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.451 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.451 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.450 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.451 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.449 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.449 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.450 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.454 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.452 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.270 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.270 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.300 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.368 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.301 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.370 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.377 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.530 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.379 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.539 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.381 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.538 | 7 reaches / 1 drops |
