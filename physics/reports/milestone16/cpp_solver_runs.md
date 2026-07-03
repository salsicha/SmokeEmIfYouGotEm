# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.061 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.088 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.070 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.092 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.068 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.094 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.067 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.101 | no |
| canonical | constriction | reduced | 9 | PASS | 0.064 | no |
| canonical | constriction | finite_volume | 9 | PASS | 4.928 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.065 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.114 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.069 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.096 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.070 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.105 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.417 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.751 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.422 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.764 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.427 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.762 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.422 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.789 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.450 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.771 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.431 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.841 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.126 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.203 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.126 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.194 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.122 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.198 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.212 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.388 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.217 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.390 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.212 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.397 | 7 reaches / 1 drops |
