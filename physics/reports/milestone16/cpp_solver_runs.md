# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.035 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.066 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.038 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.066 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.037 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.068 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.038 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.067 | no |
| canonical | constriction | reduced | 9 | PASS | 0.035 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.071 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.032 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.065 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.037 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.066 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.037 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.067 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.310 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.642 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.318 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.648 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.320 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.648 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.312 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.643 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.319 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.647 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.317 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.645 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.081 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.152 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.081 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.165 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.081 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.150 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.152 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.305 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.150 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.308 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.150 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.307 | 7 reaches / 1 drops |
