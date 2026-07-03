# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.057 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.087 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.062 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.092 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.062 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.090 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.061 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.094 | no |
| canonical | constriction | reduced | 9 | PASS | 0.059 | no |
| canonical | constriction | finite_volume | 9 | PASS | 5.139 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.058 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.108 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.063 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.092 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.064 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.097 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.360 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.748 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.402 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.723 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.394 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.787 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.384 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.772 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.376 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.802 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.377 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.795 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.099 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.172 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.099 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.173 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.099 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.172 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.170 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.354 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.170 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.338 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.172 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.357 | 7 reaches / 1 drops |
