# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.225 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.274 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.221 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.243 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.224 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.251 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.219 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.250 | no |
| canonical | constriction | reduced | 9 | PASS | 0.205 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.214 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.223 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.263 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.219 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.243 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.214 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.251 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.412 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.411 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.413 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.420 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.416 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.414 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.414 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.413 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.414 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.413 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.531 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.825 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.263 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.329 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.263 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.329 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.267 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.330 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.341 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.493 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.341 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.498 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.341 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.501 | 7 reaches / 1 drops |
