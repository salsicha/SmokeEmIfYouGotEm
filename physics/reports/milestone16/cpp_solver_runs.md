# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.289 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.348 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.290 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.315 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.293 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.318 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.291 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.320 | no |
| canonical | constriction | reduced | 9 | PASS | 0.276 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.275 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.282 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.327 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.289 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.314 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.276 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.323 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.484 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.485 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.488 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.489 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.484 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.484 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.486 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.481 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.486 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.482 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.486 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.483 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.302 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.302 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.303 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.304 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.304 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.305 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | FAIL | 0.355 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.563 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | FAIL | 0.357 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.565 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | FAIL | 0.357 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.572 | 7 reaches / 1 drops |
