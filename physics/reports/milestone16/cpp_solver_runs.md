# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.282 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.357 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.284 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.307 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.286 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.313 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.283 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.313 | no |
| canonical | constriction | reduced | 9 | PASS | 0.269 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.267 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.275 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.321 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.282 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.305 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.271 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.319 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.476 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.476 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.478 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.482 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.481 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.479 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.490 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.480 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.479 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.479 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.481 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.475 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.297 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.297 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.296 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.297 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.299 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.298 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | FAIL | 0.346 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.555 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | FAIL | 0.350 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.557 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.406 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.562 | 7 reaches / 1 drops |
