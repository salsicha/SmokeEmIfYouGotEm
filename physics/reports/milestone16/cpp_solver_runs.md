# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.210 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.230 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.201 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.224 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.217 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.246 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.210 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.333 | no |
| canonical | constriction | reduced | 9 | PASS | 0.201 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.196 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.201 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.245 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.208 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.226 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.185 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.238 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.460 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.470 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.421 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.434 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.416 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.417 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.532 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.426 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.562 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.887 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.665 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.887 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.256 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.329 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.253 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.336 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.333 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.333 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.343 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.513 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.343 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.517 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.445 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.520 | 7 reaches / 1 drops |
