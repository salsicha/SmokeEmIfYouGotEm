# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.059 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.088 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.062 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.086 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.059 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.089 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.062 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.147 | no |
| canonical | constriction | reduced | 9 | PASS | 0.094 | no |
| canonical | constriction | finite_volume | 9 | PASS | 5.002 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.064 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.200 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.065 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.094 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.064 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.101 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.360 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.730 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.443 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.735 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.426 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.794 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.362 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.718 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.448 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.719 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.366 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.793 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.108 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.187 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.109 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.177 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.100 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.173 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.169 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.353 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.176 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.340 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.170 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.345 | 7 reaches / 1 drops |
