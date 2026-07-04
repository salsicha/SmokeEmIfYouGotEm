# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.250 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.269 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.253 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.272 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.253 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.278 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.250 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.279 | no |
| canonical | constriction | reduced | 9 | PASS | 0.237 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.235 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.243 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.287 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.249 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.272 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.233 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.279 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.446 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.443 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.447 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.449 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.445 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.449 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.443 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.447 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.448 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.445 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.444 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.449 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.295 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.360 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.295 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.361 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.298 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.361 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.369 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.526 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.371 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.528 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.372 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.531 | 7 reaches / 1 drops |
