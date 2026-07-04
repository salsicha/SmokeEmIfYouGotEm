# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.281 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.289 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.268 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.293 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.272 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.297 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.268 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.297 | no |
| canonical | constriction | reduced | 9 | PASS | 0.255 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.255 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.261 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.306 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.268 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.292 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.253 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.299 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.461 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.466 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.467 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.464 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.464 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.465 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.460 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.468 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.469 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.465 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.464 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.467 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.284 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.282 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.283 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.282 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.282 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.284 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.386 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.543 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.389 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.542 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.390 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.550 | 7 reaches / 1 drops |
