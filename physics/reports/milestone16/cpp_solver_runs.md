# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.267 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.288 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.267 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.289 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.270 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.295 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.266 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.296 | no |
| canonical | constriction | reduced | 9 | PASS | 0.253 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.251 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.259 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.303 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.264 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.288 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.251 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.297 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.459 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.461 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.460 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.460 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.461 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.461 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.459 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.459 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.462 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.462 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.467 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.463 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.283 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.280 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.279 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.281 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.347 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.388 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.385 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.546 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.389 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.560 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.389 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.549 | 7 reaches / 1 drops |
