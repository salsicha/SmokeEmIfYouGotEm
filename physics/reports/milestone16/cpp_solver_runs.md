# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.254 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.273 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.253 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.275 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.256 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.283 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.254 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.285 | no |
| canonical | constriction | reduced | 9 | PASS | 0.241 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.239 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.248 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.292 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.251 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.276 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.238 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.284 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.449 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.446 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.446 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.449 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.445 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.447 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.450 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.448 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.446 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.451 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.451 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.450 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.268 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.363 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.297 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.368 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.299 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.368 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.375 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.526 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.373 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.530 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.374 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.535 | 7 reaches / 1 drops |
