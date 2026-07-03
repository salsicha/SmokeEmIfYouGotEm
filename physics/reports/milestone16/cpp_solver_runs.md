# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.113 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.139 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.123 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.145 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.122 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.155 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.191 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.160 | no |
| canonical | constriction | reduced | 9 | PASS | 0.112 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.108 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.117 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.160 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.117 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.144 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.102 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.154 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.340 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.400 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.436 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.811 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.542 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.816 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.560 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.782 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.471 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.894 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.469 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.851 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.198 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.244 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.273 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.270 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.174 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.258 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.257 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.432 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.263 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.537 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.266 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.437 | 7 reaches / 1 drops |
