# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.100 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.124 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.102 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.126 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.112 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.133 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.103 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.135 | no |
| canonical | constriction | reduced | 9 | PASS | 0.087 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.095 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.099 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.148 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.102 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.130 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.090 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.156 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.381 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.321 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.445 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.761 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.542 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.773 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.458 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.842 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.461 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.788 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.539 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.864 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.165 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.232 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.155 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.289 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.173 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.230 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.235 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.420 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.254 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.514 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.244 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.428 | 7 reaches / 1 drops |
