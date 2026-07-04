# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.267 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.286 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.265 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.291 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.271 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.294 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.262 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.294 | no |
| canonical | constriction | reduced | 9 | PASS | 0.250 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.250 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.257 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.302 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.262 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.286 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.249 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.335 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.457 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.461 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.465 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.459 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.461 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.459 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.456 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.461 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.461 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.460 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.463 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.460 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.279 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.278 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.277 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.280 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.313 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.377 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.384 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.537 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.387 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.551 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.388 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.545 | 7 reaches / 1 drops |
